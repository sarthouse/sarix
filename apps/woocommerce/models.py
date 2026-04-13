from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class WooStoreStatus(models.TextChoices):
    PENDING = 'pending', 'Pendiente'
    PROCESSING = 'processing', 'Procesando'
    ON_HOLD = 'on-hold', 'En espera'
    COMPLETED = 'completed', 'Completado'
    CANCELLED = 'cancelled', 'Cancelado'
    REFUNDED = 'refunded', 'Reembolsado'
    FAILED = 'failed', 'Fallido'


class WooStore(models.Model):
    """Configuración de tienda WooCommerce"""
    name = models.CharField(max_length=100)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)
    url = models.URLField(help_text='URL de la tienda WooCommerce (sin tailing /)')
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    webhook_secret = models.CharField(
        max_length=100,
        blank=True,
        help_text='Secreto para verificar firmas HMAC de webhooks'
    )
    is_active = models.BooleanField(default=True)
    
    sync_products = models.BooleanField(default=True, help_text='Sincronizar productos')
    sync_orders = models.BooleanField(default=True, help_text='Sincronizar órdenes')
    sync_customers = models.BooleanField(default=True, help_text='Sincronizar clientes')
    sync_categories = models.BooleanField(default=True, help_text='Sincronizar categorías')
    sync_coupons = models.BooleanField(default=True, help_text='Sincronizar cupones')
    sync_orders_status = models.JSONField(
        default=dict,
        help_text='Mapeo de estados WooCommerce a Sarix'
    )
    
    #-default status mapping
    def get_default_status_map(self):
        return {
            'pending': 'draft',
            'processing': 'confirmed',
            'on-hold': 'draft',
            'completed': 'delivered',
            'cancelled': 'cancelled',
            'refunded': 'cancelled',
            'failed': 'cancelled',
            'trash': 'cancelled'
        }
    
    def get_status_map(self):
        if not self.sync_orders_status:
            return self.get_default_status_map()
        return self.sync_orders_status
    
    last_sync_products = models.DateTimeField(null=True, blank=True)
    last_sync_orders = models.DateTimeField(null=True, blank=True)
    last_sync_customers = models.DateTimeField(null=True, blank=True)
    last_sync_categories = models.DateTimeField(null=True, blank=True)
    last_sync_coupons = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tienda WooCommerce'
        verbose_name_plural = 'Tiendas WooCommerce'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def clean(self):
        if not self.url.startswith(('http://', 'https://')):
            raise ValidationError("La URL debe comenzar con http:// o https://")


class WooProductMap(models.Model):
    woo_store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='product_maps')
    woo_product_id = models.IntegerField()
    product_template = models.ForeignKey(
        'inventory.ProductTemplate',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='woo_maps'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='woo_maps'
    )
    variation_id = models.IntegerField(null=True, blank=True)
    woo_sku = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Mapping de Producto'
        verbose_name_plural = 'Mappings de Productos'
        unique_together = [['woo_store', 'woo_product_id', 'variation_id']]
    
    def __str__(self):
        return f"Woo {self.woo_product_id} → {self.product.sku if self.product else self.product_template.sku}"


class WooCategoryMap(models.Model):
    woo_store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='category_maps')
    woo_category_id = models.IntegerField()
    category = models.ForeignKey(
        'inventory.Category',
        on_delete=models.CASCADE,
        related_name='woo_maps'
    )
    
    class Meta:
        verbose_name = 'Mapping de Categoría'
        verbose_name_plural = 'Mappings de Categorías'
        unique_together = [['woo_store', 'woo_category_id']]
    
    def __str__(self):
        return f"WooCat {self.woo_category_id} → {self.category.name}"


class WooCustomerMap(models.Model):
    woo_store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='customer_maps')
    woo_customer_id = models.IntegerField()
    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE, related_name='woo_maps')
    
    class Meta:
        verbose_name = 'Mapping de Cliente'
        verbose_name_plural = 'Mappings de Clientes'
        unique_together = [['woo_store', 'woo_customer_id']]
    
    def __str__(self):
        return f"WooCust {self.woo_customer_id} → {self.partner.name}"


class WooOrderMap(models.Model):
    woo_store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='order_maps')
    woo_order_id = models.IntegerField()
    sale_order = models.ForeignKey('sales.SaleOrder', on_delete=models.CASCADE, related_name='woo_maps')
    
    class Meta:
        verbose_name = 'Mapping de Orden'
        verbose_name_plural = 'Mappings de Órdenes'
        unique_together = [['woo_store', 'woo_order_id']]
    
    def __str__(self):
        return f"WooOrd {self.woo_order_id} → {self.sale_order.number}"


class WooCouponMap(models.Model):
    woo_store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='coupon_maps')
    woo_coupon_id = models.IntegerField()
    coupon_code = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Porcentaje'),
        ('fixed', 'Fijo'),
    ], default='percentage')
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Mapping de Cupón'
        verbose_name_plural = 'Mappings de Cupones'
        unique_together = [['woo_store', 'woo_coupon_id']]
    
    def __str__(self):
        return f"WooCoupon {self.coupon_code}"


class WooTaxMapping(models.Model):
    woo_store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='tax_maps')
    woo_tax_class = models.CharField(max_length=50, help_text='tax_class de WooCommerce (ej: standard, reduced-rate)')
    tax = models.ForeignKey('taxes.Tax', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Mapping de Impuesto'
        verbose_name_plural = 'Mappings de Impuestos'
        unique_together = [['woo_store', 'woo_tax_class']]
    
    def __str__(self):
        return f"WooTax {self.woo_tax_class} → {self.tax.name}"


class WooWebhookLog(models.Model):
    """Log de webhooks recibidos de WooCommerce"""
    store = models.ForeignKey('WooStore', on_delete=models.CASCADE, related_name='webhook_logs')
    topic = models.CharField(max_length=50, help_text='Topic del webhook (ej: order.created)')
    delivery_id = models.CharField(max_length=50, help_text='ID de entrega de WooCommerce')
    payload = models.JSONField(null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Log de Webhook'
        verbose_name_plural = 'Logs de Webhooks'
        ordering = ['-processed_at']

    def __str__(self):
        return f"{self.topic} - {self.delivery_id} - {'OK' if self.success else 'ERROR'}"
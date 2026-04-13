from django.db import models
from django.conf import settings
from django.utils import timezone


class SaleOrderStatus(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    CONFIRMED = 'confirmed', 'Confirmada'
    DELIVERED = 'delivered', 'Entregada'
    INVOICED = 'invoiced', 'Facturada'
    CANCELLED = 'cancelled', 'Anulada'


class SaleOrder(models.Model):
    number = models.CharField(max_length=20, unique=True, blank=True)
    prefix = models.CharField(max_length=5, default='VTA')
    customer = models.ForeignKey(
        'partners.Partner',
        on_delete=models.PROTECT,
        related_name='sale_orders',
        limit_choices_to={'is_customer': True}
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.PROTECT,
        related_name='sale_orders'
    )
    status = models.CharField(
        max_length=20,
        choices=SaleOrderStatus.choices,
        default=SaleOrderStatus.DRAFT
    )
    date = models.DateField()
    invoice_ids = models.ManyToManyField(
        'accounting.Journal',
        blank=True,
        related_name='sale_orders',
        help_text='Facturas vinculadas a esta orden'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sale_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    invoiced_at = models.DateTimeField(null=True, blank=True)
    woo_metadata = models.JSONField(null=True, blank=True, help_text='Metadata de WooCommerce (meta_data de la orden)')
    woo_order_id = models.IntegerField(null=True, blank=True, help_text='ID de la orden en WooCommerce')

    class Meta:
        verbose_name = 'Orden de Venta'
        verbose_name_plural = 'Ordenes de Venta'
        ordering = ['-date', '-number']

    def __str__(self):
        return f"{self.number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from django.db.models import Max
        year = self.date.year
        prefix_str = f"{self.prefix}-{year}-"
        last = SaleOrder.objects.filter(
            number__startswith=prefix_str
        ).aggregate(Max('number'))
        last_num = last.get('number__max', None)
        if last_num and last_num.startswith(prefix_str):
            seq = int(last_num.split('-')[-1]) + 1
        else:
            seq = 1
        return f"{prefix_str}{seq:06d}"

    @property
    def subtotal(self):
        return sum(line.subtotal for line in self.lines.all())

    @property
    def amount_tax(self):
        return sum(line.amount_tax for line in self.lines.all())

    @property
    def total(self):
        return self.subtotal + self.amount_tax

    @property
    def total_qty(self):
        return sum(line.qty for line in self.lines.all())


class DiscountType(models.TextChoices):
    PERCENTAGE = 'percentage', 'Porcentaje'
    FIXED = 'fixed', 'Fijo'


class SaleOrderLine(models.Model):
    order = models.ForeignKey(
        SaleOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='sale_lines'
    )
    qty = models.DecimalField(max_digits=14, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        null=True, blank=True
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    taxes = models.ManyToManyField(
        'taxes.Tax',
        related_name='sale_order_lines',
        blank=True,
        help_text='Impuestos aplicados a esta línea'
    )
    woo_line_metadata = models.JSONField(null=True, blank=True, help_text='Metadata de WooCommerce (atributos, etc)')

    class Meta:
        verbose_name = 'Linea de Orden'
        verbose_name_plural = 'Lineas de Orden'

    def __str__(self):
        return f"{self.order.number} - {self.product.sku}"

    @property
    def discount(self):
        if self.discount_type == DiscountType.PERCENTAGE:
            return (self.unit_price * self.qty) * (self.discount_value / 100)
        elif self.discount_type == DiscountType.FIXED:
            return self.discount_value
        return 0

    @property
    def subtotal(self):
        return (self.unit_price * self.qty) - self.discount

    @property
    def amount_tax(self):
        total = 0
        for tax in self.taxes.all():
            if tax.amount_type == 'percent':
                total += self.subtotal * (tax.amount / 100)
            elif tax.amount_type == 'fixed':
                total += tax.amount * self.qty
        return total

    @property
    def amount_total(self):
        return self.subtotal + self.amount_tax


class SaleQuoteStatus(models.TextChoices):
    BUDGET = 'budget', 'Presupuesto'
    ACCEPTED = 'accepted', 'Aceptado'
    REJECTED = 'rejected', 'Rechazado'
    EXPIRED = 'expired', 'Vencido'


class SaleQuote(models.Model):
    number = models.CharField(max_length=20, unique=True, blank=True)
    prefix = models.CharField(max_length=5, default='PTO')
    customer = models.ForeignKey(
        'partners.Partner',
        on_delete=models.PROTECT,
        related_name='sale_quotes',
        limit_choices_to={'is_customer': True}
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.PROTECT,
        related_name='sale_quotes'
    )
    status = models.CharField(
        max_length=20,
        choices=SaleQuoteStatus.choices,
        default=SaleQuoteStatus.BUDGET
    )
    valid_until = models.DateField()
    date = models.DateField()
    sale_order = models.ForeignKey(
        SaleOrder,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='quote'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sale_quotes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-date', '-number']

    def __str__(self):
        return f"{self.number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from django.db.models import Max
        year = self.date.year
        prefix_str = f"{self.prefix}-{year}-"
        last = SaleQuote.objects.filter(
            number__startswith=prefix_str
        ).aggregate(Max('number'))
        last_num = last.get('number__max', None)
        if last_num and last_num.startswith(prefix_str):
            seq = int(last_num.split('-')[-1]) + 1
        else:
            seq = 1
        return f"{prefix_str}{seq:06d}"

    @property
    def is_valid(self):
        from datetime import date
        return self.valid_until >= date.today() and self.status == self.BUDGET

    @property
    def subtotal(self):
        return sum(line.subtotal for line in self.lines.all())

    @property
    def amount_tax(self):
        return sum(line.amount_tax for line in self.lines.all())

    @property
    def total(self):
        return self.subtotal + self.amount_tax


class SaleQuoteLine(models.Model):
    quote = models.ForeignKey(
        SaleQuote,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='quote_lines'
    )
    qty = models.DecimalField(max_digits=14, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        null=True, blank=True
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    taxes = models.ManyToManyField(
        'taxes.Tax',
        related_name='sale_quote_lines',
        blank=True,
        help_text='Impuestos aplicados a esta línea'
    )

    class Meta:
        verbose_name = 'Linea de Presupuesto'
        verbose_name_plural = 'Lineas de Presupuesto'

    def __str__(self):
        return f"{self.quote.number} - {self.product.sku}"

    @property
    def discount(self):
        if self.discount_type == DiscountType.PERCENTAGE:
            return (self.unit_price * self.qty) * (self.discount_value / 100)
        elif self.discount_type == DiscountType.FIXED:
            return self.discount_value

    @property
    def subtotal(self):
        return (self.unit_price * self.qty) - self.discount

    @property
    def amount_tax(self):
        total = 0
        for tax in self.taxes.all():
            if tax.amount_type == 'percent':
                total += self.subtotal * (tax.amount / 100)
            elif tax.amount_type == 'fixed':
                total += tax.amount * self.qty
        return total

    @property
    def amount_total(self):
        return self.subtotal + self.amount_tax
        return 0

    @property
    def subtotal(self):
        return (self.unit_price * self.qty) - self.discount
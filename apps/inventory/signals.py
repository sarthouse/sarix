from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import StockMovement, Stock, Product, StockQuant, StockCache
from .services import StockAlertService, StockCacheManager


@receiver(post_save, sender=StockMovement)
def on_movement_posted(sender, instance, **kwargs):
    """Cuando se publica un movimiento, checkar alertas + invalida caché"""
    if instance.status == 'posted':
        product = instance.product
        if product.product_type != 'servicio':
            try:
                stock = Stock.objects.get(product=product, warehouse=instance.warehouse_dst or instance.warehouse_src)
                StockAlertService.check(stock)
            except Stock.DoesNotExist:
                pass
        
        # Invalida caché de stock
        if instance.warehouse_src_id:
            StockCacheManager.invalidate(product.id, instance.warehouse_src_id)
        if instance.warehouse_dst_id:
            StockCacheManager.invalidate(product.id, instance.warehouse_dst_id)


@receiver(post_save, sender=Stock)
def on_stock_changed(sender, instance, **kwargs):
    """Cuando cambia stock, checkar alertas + invalida caché"""
    if instance.product.product_type != 'servicio':
        StockAlertService.check(instance)
    
    # Invalida caché
    StockCacheManager.invalidate(instance.product.id, instance.warehouse.id)


@receiver(post_save, sender=StockQuant)
def on_stock_quant_changed(sender, instance, **kwargs):
    """Cuando cambia StockQuant, invalida caché"""
    if instance.product and instance.warehouse:
        StockCacheManager.invalidate(instance.product.id, instance.warehouse.id)


@receiver(post_save, sender=StockCache)
def on_stock_cache_updated(sender, instance, **kwargs):
    """Cuando StockCache se actualiza, invalida caché en memoria"""
    StockCacheManager.invalidate(instance.product.id, instance.warehouse.id)


@receiver(post_save, sender=Product)
def on_product_created(sender, instance, **kwargs):
    """Cuando se crea un producto, crear Stock default si es almacenable."""
    if instance.product_type == 'almacenable':
        from .models import Warehouse
        warehouses = Warehouse.objects.filter(is_active=True)
        for warehouse in warehouses:
            Stock.objects.get_or_create(
                product=instance,
                warehouse=warehouse,
                defaults={'qty_available': 0, 'qty_reserved': 0, 'qty_min': 0}
            )
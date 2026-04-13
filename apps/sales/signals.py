from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SaleOrder, SaleOrderStatus


@receiver(post_save, sender=SaleOrder)
def on_order_invoiced(sender, instance, **kwargs):
    """Cuando se factura una orden, podria generar alertas o notifications."""
    if instance.status == SaleOrderStatus.INVOICED:
        pass
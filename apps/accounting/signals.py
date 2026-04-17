from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Journal, JournalLine, JournalStatus


@receiver(post_save, sender=Journal)
def invalidate_cache_on_post(sender, instance, **kwargs):
    """Invalida caché de reportes cuando se publica asiento"""
    if instance.status == JournalStatus.POSTED:
        from .tasks import invalidate_report_cache
        invalidate_report_cache.delay()
    
    # Invalida caché de saldos de cuentas
    if instance.period_id:
        cache.delete(f"account_balance:period:{instance.period_id}")


@receiver(post_save, sender=JournalLine)
def invalidate_account_balance_cache(sender, instance, **kwargs):
    """Invalida caché de saldos cuando cambia línea de asiento"""
    if instance.account_id and instance.journal_id:
        period_id = instance.journal.period_id
        cache_key = f"account_balance:{instance.account_id}:{period_id}"
        cache.delete(cache_key)

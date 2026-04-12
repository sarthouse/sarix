from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Journal, JournalStatus

@receiver(post_save, sender=Journal)
def invalidate_cache_on_post(sender, instance, **kwargs):
    if instance.status == JournalStatus.POSTED:
        from .tasks import invalidate_report_cache
        invalidate_report_cache.delay()

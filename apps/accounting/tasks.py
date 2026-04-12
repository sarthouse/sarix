from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def generate_balance_report(self, date:str):
    cache_key = f"reports:balance:{date}"
    try:
        from apps.reports.views import BalanceSheetView
        data = BalanceSheetView.get_raw_data(up_to_date=date)
        cache.set(cache_key, data, timeout=60 * 60)
        return {"ok":True, "date":date}
    except Exception as exc:
        logger.error(f"Error generando balance: {exc}")
        raise self.retry(exc=exc, countdown=60)
    
@shared_task(bind=True, max_retries=3)
def export_journals_to_excel(self, filters: dict):
    try:
        import openpyxl
        from apps.accounting.models import Journal
        from django.core.files.storage import default_storage

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asientos"

        ws.append(["Número", "Fecha", "Descripción", "Referencia", "Estado", "Periodo"])

        queryset = Journal.objects.filter(**filters).order_by("date", "number")
        for journal in queryset:
            ws.append([
                journal.number,
                str(journal.date),
                journal.description,
                journal.reference,
                journal.get_status_display(),
                str(journal.period)
            ])
        
        filename = f"exports/journals_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with default_storage.open(filename, "wb") as f:
            wb.save(f)
        
        return {"ok": True, "file": filename}
    except Exception as exc:
        logger.error(f"Error exportando journals: {exc}")
        raise self.retry(exc=exc, countdown=30)

@shared_task
def invalidate_report_cache():
    cache.delete_pattern("reports:*")
    logger.info("Cache de reportes invalidada")
    return {"ok":True}
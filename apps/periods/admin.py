from django.contrib import admin
from .models import FiscalYear, AccountingPeriod

@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "is_closed"]
    list_filter = ["is_closed"]
    search_fields = ["name"]

@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ["name", "fiscal_year", "start_date", "end_date", "is_closed"]
    list_filter = ["fiscal_year", "is_closed"]
    search_fields = ["name"]
from django.contrib import admin
from .models import Payment, PaymentLine, Check, CheckOperation


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'partner', 'payment_type', 'method_type', 'amount', 'date', 'state']
    list_filter = ['payment_type', 'method_type', 'state', 'currency']
    search_fields = ['partner__name', 'reference']
    date_hierarchy = 'date'


@admin.register(PaymentLine)
class PaymentLineAdmin(admin.ModelAdmin):
    list_display = ['payment', 'invoice', 'amount', 'reconciled']
    list_filter = ['reconciled']


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ['number', 'partner', 'check_type', 'amount', 'issue_date', 'state']
    list_filter = ['check_type', 'state', 'currency']
    search_fields = ['number', 'partner__name']


@admin.register(CheckOperation)
class CheckOperationAdmin(admin.ModelAdmin):
    list_display = ['check', 'operation_type', 'partner', 'date']
    list_filter = ['operation_type']
    date_hierarchy = 'date'
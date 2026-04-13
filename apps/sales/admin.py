from django.contrib import admin
from .models import SaleOrder, SaleOrderLine, SaleQuote, SaleQuoteLine


class SaleOrderLineInline(admin.TabularInline):
    model = SaleOrderLine
    extra = 1


class SaleQuoteLineInline(admin.TabularInline):
    model = SaleQuoteLine
    extra = 1


@admin.register(SaleOrder)
class SaleOrderAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer', 'status', 'date', 'total']
    list_filter = ['status', 'date']
    search_fields = ['number', 'customer__name']
    inlines = [SaleOrderLineInline]
    readonly_fields = ['number', 'subtotal', 'total']


@admin.register(SaleQuote)
class SaleQuoteAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer', 'status', 'date', 'valid_until', 'total']
    list_filter = ['status', 'valid_until']
    search_fields = ['number', 'customer__name']
    inlines = [SaleQuoteLineInline]
    readonly_fields = ['number', 'subtotal', 'total', 'is_valid', 'sale_order']
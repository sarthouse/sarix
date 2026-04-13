from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderPartnerLine


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    fields = ['product', 'template', 'name', 'qty', 'price_unit', 'taxes', 'date_planned', 'qty_received', 'qty_invoiced']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['name', 'partner', 'warehouse', 'state', 'date_order', 'amount_total']
    list_filter = ['state', 'date_order', 'warehouse']
    search_fields = ['name', 'partner__name', 'partner_ref']
    inlines = [PurchaseOrderLineInline]
    readonly_fields = ['name', 'amount_untaxed', 'amount_tax', 'amount_total', 'invoiced_status', 'receipt_status']


@admin.register(PurchaseOrderPartnerLine)
class PurchaseOrderPartnerLineAdmin(admin.ModelAdmin):
    list_display = ['partner', 'product_template', 'product_code', 'min_qty', 'price', 'currency']
    list_filter = ['partner', 'currency']
    search_fields = ['partner__name', 'product_template__sku', 'product_code']
from django.contrib import admin
from .models import (
    Category, Attribute, AttributeValue, ProductTag, UnitOfMeasure,
    ProductTemplate, Product, Lot, StockQuant,
    Warehouse, Location, PickingType, Stock, StockMovement, StockAlert
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    search_fields = ['name']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'symbol', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'woo_attribute_id']
    search_fields = ['name']


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'woo_term_id']
    list_filter = ['attribute']


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'woo_tag_id']
    search_fields = ['name', 'slug']


@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'product_type', 'is_active']
    list_filter = ['product_type', 'category', 'is_active']
    search_fields = ['sku', 'name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'template', 'name', 'is_active']
    list_filter = ['template', 'is_active']
    search_fields = ['sku', 'name']


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ['number', 'template', 'location', 'date_in', 'expiry_date', 'is_active']
    list_filter = ['location__warehouse', 'template']
    search_fields = ['number']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'warehouse', 'location_type', 'is_active']
    list_filter = ['warehouse', 'location_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(PickingType)
class PickingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'warehouse', 'color', 'is_active']
    list_filter = ['warehouse', 'code', 'is_active']
    search_fields = ['name', 'code']


@admin.register(StockQuant)
class StockQuantAdmin(admin.ModelAdmin):
    list_display = ['product', 'lot', 'location', 'quantity', 'reserved', 'available']
    list_filter = ['location__warehouse', 'product']
    search_fields = ['product__sku', 'lot__number']
    
    readonly_fields = ['available']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'partner', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['template', 'product', 'warehouse', 'qty_available', 'qty_reserved']
    list_filter = ['warehouse']
    search_fields = ['template__sku', 'product__sku']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['number', 'movement_type', 'product', 'qty', 'qty_done', 'status', 'location_src', 'location_dst']
    list_filter = ['movement_type', 'status', 'picking_type']
    search_fields = ['number', 'product__sku', 'origin']
    readonly_fields = ['number', 'journal', 'qty_done']
    
    fieldsets = (
        ('General', {
            'fields': ('number', 'movement_type', 'picking_type', 'status')
        }),
        ('Producto', {
            'fields': ('template', 'product', 'lot', 'lot_name')
        }),
        ('Ubicaciones', {
            'fields': ('location_src', 'location_dst', 'warehouse_src', 'warehouse_dst')
        }),
        ('Cantidad', {
            'fields': ('qty', 'qty_done', 'uom', 'unit_cost')
        }),
        ('Origen', {
            'fields': ('origin', 'partner', 'reference')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'quant', 'resolved', 'created_at']
    list_filter = ['alert_type', 'resolved']
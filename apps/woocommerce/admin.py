from django.contrib import admin
from .models import (
    WooStore, WooProductMap, WooCategoryMap,
    WooCustomerMap, WooOrderMap, WooCouponMap, WooTaxMapping,
    WooWebhookLog
)


@admin.register(WooStore)
class WooStoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'url', 'is_active', 'last_sync_products', 'last_sync_orders']
    list_filter = ['is_active', 'company']
    search_fields = ['name', 'url']
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'company', 'url', 'is_active')
        }),
        ('Credenciales API', {
            'fields': ('consumer_key', 'consumer_secret', 'webhook_secret'),
            'classes': ('collapse',)
        }),
        ('Sincronización', {
            'fields': ('sync_products', 'sync_orders', 'sync_customers', 'sync_categories', 'sync_coupons', 'sync_orders_status')
        }),
        ('Última Sincronización', {
            'fields': ('last_sync_products', 'last_sync_orders', 'last_sync_customers', 'last_sync_categories', 'last_sync_coupons'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WooProductMap)
class WooProductMapAdmin(admin.ModelAdmin):
    list_display = ['woo_product_id', 'product', 'product_template', 'variation_id']
    list_filter = ['woo_store']
    search_fields = ['woo_product_id', 'product__sku', 'product_template__sku']


@admin.register(WooCategoryMap)
class WooCategoryMapAdmin(admin.ModelAdmin):
    list_display = ['woo_category_id', 'category']
    list_filter = ['woo_store']


@admin.register(WooCustomerMap)
class WooCustomerMapAdmin(admin.ModelAdmin):
    list_display = ['woo_customer_id', 'partner']
    list_filter = ['woo_store']


@admin.register(WooOrderMap)
class WooOrderMapAdmin(admin.ModelAdmin):
    list_display = ['woo_order_id', 'sale_order']
    list_filter = ['woo_store']


@admin.register(WooCouponMap)
class WooCouponMapAdmin(admin.ModelAdmin):
    list_display = ['woo_coupon_id', 'coupon_code', 'discount_type', 'discount_value', 'is_active']
    list_filter = ['woo_store', 'is_active']


@admin.register(WooTaxMapping)
class WooTaxMappingAdmin(admin.ModelAdmin):
    list_display = ['woo_store', 'woo_tax_class', 'tax']
    list_filter = ['woo_store']


@admin.register(WooWebhookLog)
class WooWebhookLogAdmin(admin.ModelAdmin):
    list_display = ['store', 'topic', 'delivery_id', 'success', 'processed_at']
    list_filter = ['store', 'topic', 'success']
    search_fields = ['delivery_id', 'error']
    readonly_fields = ['store', 'topic', 'delivery_id', 'payload', 'processed_at', 'success', 'error']
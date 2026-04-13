from rest_framework import serializers
from .models import (
    WooStore, WooProductMap, WooCategoryMap, 
    WooCustomerMap, WooOrderMap, WooCouponMap, WooTaxMapping,
    WooWebhookLog
)


class WooStoreSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    product_maps_count = serializers.SerializerMethodField()
    order_maps_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WooStore
        fields = [
            'id', 'name', 'company', 'company_name',
            'url', 'consumer_key', 'consumer_secret', 'webhook_secret', 'is_active',
            'sync_products', 'sync_orders', 'sync_customers', 
            'sync_categories', 'sync_coupons', 'sync_orders_status',
            'last_sync_products', 'last_sync_orders', 'last_sync_customers',
            'last_sync_categories', 'last_sync_coupons',
            'created_at', 'updated_at',
            'product_maps_count', 'order_maps_count'
        ]
        extra_kwargs = {
            'consumer_secret': {'write_only': True},
            'webhook_secret': {'write_only': True}
        }
    
    def get_product_maps_count(self, obj):
        return obj.product_maps.count()
    
    def get_order_maps_count(self, obj):
        return obj.order_maps.count()


class WooProductMapSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    template_name = serializers.CharField(source='product_template.name', read_only=True)
    template_sku = serializers.CharField(source='product_template.sku', read_only=True)
    
    class Meta:
        model = WooProductMap
        fields = [
            'id', 'woo_store', 'woo_product_id', 
            'product_template', 'template_name', 'template_sku',
            'product', 'product_name', 'product_sku',
            'variation_id', 'woo_sku'
        ]


class WooCategoryMapSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = WooCategoryMap
        fields = ['id', 'woo_store', 'woo_category_id', 'category', 'category_name']


class WooCustomerMapSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    partner_email = serializers.CharField(source='partner.email', read_only=True)
    
    class Meta:
        model = WooCustomerMap
        fields = ['id', 'woo_store', 'woo_customer_id', 'partner', 'partner_name', 'partner_email']


class WooOrderMapSerializer(serializers.ModelSerializer):
    sale_order_number = serializers.CharField(source='sale_order.number', read_only=True)
    sale_order_status = serializers.CharField(source='sale_order.status', read_only=True)
    sale_order_total = serializers.DecimalField(
        source='sale_order.total', max_digits=12, decimal_places=2, read_only=True
    )
    woo_metadata = serializers.JSONField(source='sale_order.woo_metadata', read_only=True)
    woo_order_id = serializers.IntegerField(source='sale_order.woo_order_id', read_only=True)
    
    class Meta:
        model = WooOrderMap
        fields = [
            'id', 'woo_store', 'woo_order_id', 
            'sale_order', 'sale_order_number', 'sale_order_status', 'sale_order_total',
            'woo_metadata'
        ]


class WooCouponMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = WooCouponMap
        fields = ['id', 'woo_store', 'woo_coupon_id', 'coupon_code', 'discount_type', 'discount_value', 'is_active']


class WooTaxMappingSerializer(serializers.ModelSerializer):
    tax_name = serializers.CharField(source='tax.name', read_only=True)
    
    class Meta:
        model = WooTaxMapping
        fields = ['id', 'woo_store', 'woo_tax_class', 'tax', 'tax_name']


class WooWebhookLogSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    class Meta:
        model = WooWebhookLog
        fields = ['id', 'store', 'store_name', 'topic', 'delivery_id', 'payload', 'processed_at', 'success', 'error']


class SyncResultSerializer(serializers.Serializer):
    categories = serializers.DictField(required=False)
    products = serializers.DictField(required=False)
    customers = serializers.DictField(required=False)
    coupons = serializers.DictField(required=False)
    orders = serializers.DictField(required=False)
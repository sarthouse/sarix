from rest_framework import serializers
from .models import (
    Category, Attribute, AttributeValue, UnitOfMeasure,
    ProductTemplate, Product, Lot, StockQuant,
    Warehouse, Location, PickingType, Stock, StockMovement, StockAlert
)


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    
    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'value']


class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = Attribute
        fields = ['id', 'name', 'values']


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name']


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'name', 'code', 'symbol', 'category', 'ratio', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    cost_price_display = serializers.DecimalField(source='get_cost_price', max_digits=12, decimal_places=2, read_only=True)
    sale_price_display = serializers.DecimalField(source='get_sale_price', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'template', 'template_name', 'sku', 'name', 'attribute_values', 'cost_price', 'sale_price', 'cost_price_display', 'sale_price_display', 'is_active']


class ProductListSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'template_name', 'is_active']


class ProductTemplateSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    variations_count = serializers.SerializerMethodField()
    sale_taxes_display = serializers.SerializerMethodField()
    purchase_taxes_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductTemplate
        fields = ['id', 'sku', 'name', 'category', 'category_name', 'product_type', 'unit_of_measure', 'cost_price', 'sale_price', 'track_lot', 'track_variation', 'is_active', 'variations_count', 'sale_tax_ids', 'sale_taxes_display', 'purchase_tax_ids', 'purchase_taxes_display']
    
    def get_variations_count(self, obj):
        return obj.variations.count()
    
    def get_sale_taxes_display(self, obj):
        return [{'id': t.id, 'name': t.name, 'amount': t.amount} for t in obj.sale_tax_ids.all()]
    
    def get_purchase_taxes_display(self, obj):
        return [{'id': t.id, 'name': t.name, 'amount': t.amount} for t in obj.purchase_tax_ids.all()]


class ProductTemplateListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ProductTemplate
        fields = ['id', 'sku', 'name', 'category_name', 'product_type', 'is_active']


class LotSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    
    class Meta:
        model = Lot
        fields = ['id', 'number', 'template', 'template_name', 'location', 'location_code', 'warehouse_name', 'date_in', 'date_out', 'expiry_date', 'is_active']


class LocationSerializer(serializers.ModelSerializer):
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'warehouse', 'warehouse_code', 'warehouse_name', 'parent', 'parent_name', 'location_type', 'location_type_display', 'is_scrap', 'is_active', 'full_name']


class LocationListSerializer(serializers.ModelSerializer):
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)

    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'warehouse_code', 'location_type', 'location_type_display', 'is_active']


class PickingTypeSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    code_display = serializers.CharField(source='get_code_display', read_only=True)
    default_location_src_code = serializers.CharField(source='default_location_src.code', read_only=True)
    default_location_dst_code = serializers.CharField(source='default_location_dst.code', read_only=True)

    class Meta:
        model = PickingType
        fields = [
            'id', 'name', 'code', 'code_display', 'warehouse', 'warehouse_name',
            'color', 'sequence_prefix',
            'default_location_src', 'default_location_src_code',
            'default_location_dst', 'default_location_dst_code',
            'use_create_lots', 'use_existing_lots', 'allow_partial', 'show_operations', 'is_active'
        ]


class PickingTypeListSerializer(serializers.ModelSerializer):
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    code_display = serializers.CharField(source='get_code_display', read_only=True)

    class Meta:
        model = PickingType
        fields = ['id', 'name', 'code', 'code_display', 'warehouse_code', 'color', 'is_active']


class StockQuantSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_number = serializers.CharField(source='lot.number', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    warehouse_code = serializers.CharField(source='location.warehouse.code', read_only=True)
    available = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)
    
    class Meta:
        model = StockQuant
        fields = ['id', 'product', 'product_sku', 'product_name', 'lot', 'lot_number', 'location', 'location_code', 'location_name', 'warehouse_code', 'quantity', 'reserved', 'available']


class WarehouseSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    locations = LocationListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'code', 'partner', 'partner_name', 'is_active', 'locations']


class StockSerializer(serializers.ModelSerializer):
    template_sku = serializers.CharField(source='template.sku', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    qty_free = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)
    
    class Meta:
        model = Stock
        fields = ['id', 'template', 'template_sku', 'product', 'product_sku', 'warehouse', 'warehouse_code', 'qty_available', 'qty_reserved', 'qty_free', 'qty_min']


class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    template_sku = serializers.CharField(source='template.sku', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Location fields (nuevo)
    location_src_code = serializers.CharField(source='location_src.code', read_only=True)
    location_dst_code = serializers.CharField(source='location_dst.code', read_only=True)
    
    # Legacy
    warehouse_src_code = serializers.CharField(source='warehouse_src.code', read_only=True)
    warehouse_dst_code = serializers.CharField(source='warehouse_dst.code', read_only=True)
    
    # Picking type
    picking_type_name = serializers.CharField(source='picking_type.name', read_only=True)
    
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    journal_number = serializers.CharField(source='journal.number', read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    uom_code = serializers.CharField(source='uom.code', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'movement_type', 'movement_type_display', 'status', 'status_display',
            'picking_type', 'picking_type_name',
            'template', 'template_sku', 'product', 'product_sku', 'lot', 'lot_name',
            'location_src', 'location_src_code', 'location_dst', 'location_dst_code',
            'warehouse_src', 'warehouse_src_code', 'warehouse_dst', 'warehouse_dst_code',
            'qty', 'qty_done', 'uom', 'uom_code', 'unit_cost', 'total',
            'origin', 'partner', 'partner_name', 'journal', 'journal_number',
            'reference', 'notes', 'created_by', 'created_by_username', 'created_at', 'posted_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'posted_at', 'journal']


class StockMovementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            'movement_type', 'picking_type',
            'template', 'product', 'lot', 'lot_name',
            'location_src', 'location_dst',
            'warehouse_src', 'warehouse_dst',
            'qty', 'uom', 'unit_cost',
            'origin', 'partner', 'reference', 'notes',
        ]
    
    def validate(self, data):
        from django.core.exceptions import ValidationError
        movement_type = data.get('movement_type')
        location_src = data.get('location_src')
        location_dst = data.get('location_dst')
        warehouse_src = data.get('warehouse_src')
        warehouse_dst = data.get('warehouse_dst')
        
        # Validar locations/warehouses según tipo
        if movement_type in ('salida', 'transferencia') and not location_src and not warehouse_src:
            raise serializers.ValidationError({'location_src': 'Requerido para salida/transferencia'})
        
        if movement_type in ('entrada', 'ajuste', 'transferencia') and not location_dst and not warehouse_dst:
            raise serializers.ValidationError({'location_dst': 'Requerido para entrada/ajuste/transferencia'})
        
        # Validar que origen != destino para transferencia
        if movement_type == 'transferencia':
            src = location_src or warehouse_src
            dst = location_dst or warehouse_dst
            if src and dst and src == dst:
                raise serializers.ValidationError('Ubicación origen y destino deben ser diferentes')
        
        template = data.get('template')
        product = data.get('product')
        
        if template and template.product_type == 'servicio':
            if movement_type in ('entrada', 'salida', 'ajuste'):
                raise serializers.ValidationError('Los servicios no tienen stock')
        
        return data


class StockAlertSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='quant.product.sku', read_only=True)
    product_name = serializers.CharField(source='quant.product.name', read_only=True)
    location_code = serializers.CharField(source='quant.location.code', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    
    class Meta:
        model = StockAlert
        fields = [
            'id', 'quant', 'product_sku', 'product_name', 'location_code',
            'alert_type', 'alert_type_display', 'resolved', 'created_at'
        ]
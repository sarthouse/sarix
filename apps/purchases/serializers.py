from rest_framework import serializers
from .models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderPartnerLine


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    template_sku = serializers.CharField(source='template.sku', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    uom_name = serializers.CharField(source='uom.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    taxes_display = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderLine
        fields = [
            'id', 'product', 'product_sku', 'product_name',
            'template', 'template_sku', 'template_name',
            'name', 'qty', 'price_unit',
            'taxes', 'taxes_display',
            'date_planned', 'qty_received', 'qty_invoiced',
            'uom', 'uom_name', 'subtotal'
        ]

    def get_taxes_display(self, obj):
        return [tax.name for tax in obj.taxes.all()]


class PurchaseOrderLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderLine
        fields = ['product', 'template', 'name', 'qty', 'price_unit', 'taxes', 'date_planned', 'uom']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    partner_vat = serializers.CharField(source='partner.vat', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    amount_untaxed = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    picking_count = serializers.SerializerMethodField()
    invoice_count = serializers.SerializerMethodField()
    invoice_numbers = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'name', 'prefix',
            'partner', 'partner_name', 'partner_vat', 'partner_ref',
            'warehouse', 'warehouse_name',
            'state', 'state_display',
            'date_order', 'date_approve', 'date_planned',
            'currency', 'currency_code',
            'origin', 'notes',
            'lines',
            'amount_untaxed', 'amount_tax', 'amount_total',
            'picking_ids', 'picking_count',
            'invoice_ids', 'invoice_count', 'invoice_numbers',
            'invoiced_status', 'receipt_status',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_by', 'created_at', 'updated_at',
            'date_approve', 'picking_ids', 'invoice_ids'
        ]
    
    def get_picking_count(self, obj):
        return obj.picking_ids.count()
    
    def get_invoice_count(self, obj):
        return obj.invoice_ids.count()
    
    def get_invoice_numbers(self, obj):
        return [inv.number for inv in obj.invoice_ids.all()]

    def get_picking_count(self, obj):
        return obj.picking_ids.count()


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineCreateSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'partner', 'partner_ref',
            'warehouse', 'date_order', 'date_planned',
            'currency', 'origin', 'notes',
            'lines'
        ]

    def validate(self, data):
        partner = data.get('partner')
        if partner and not partner.is_supplier:
            raise serializers.ValidationError({
                'partner': 'El proveedor debe tener is_supplier=True.'
            })

        lines = data.get('lines', [])
        if not lines:
            raise serializers.ValidationError({
                'lines': 'Debe tener al menos una línea.'
            })

        return data

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        order = PurchaseOrder.objects.create(**validated_data)
        
        for line_data in lines_data:
            line = PurchaseOrderLine(order=order, **line_data)
            line.clean()
            line.save()
        
        return order


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    amount_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'name', 'partner_name', 'state', 'state_display',
            'date_order', 'amount_total', 'currency_code'
        ]


class PurchaseOrderPartnerLineSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    product_sku = serializers.CharField(source='product_template.sku', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = PurchaseOrderPartnerLine
        fields = [
            'id', 'partner', 'partner_name',
            'product_template', 'product_sku',
            'product_code', 'product_name',
            'min_qty', 'price', 'currency', 'currency_code',
            'date_start', 'date_end'
        ]


class PurchaseOrderPartnerLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderPartnerLine
        fields = [
            'partner', 'product_template',
            'product_code', 'product_name',
            'min_qty', 'price', 'currency',
            'date_start', 'date_end'
        ]
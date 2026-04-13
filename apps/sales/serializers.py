from rest_framework import serializers
from .models import SaleOrder, SaleOrderLine, SaleOrderStatus, DiscountType, SaleQuote, SaleQuoteLine, SaleQuoteStatus


class SaleOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    taxes_display = serializers.SerializerMethodField()

    class Meta:
        model = SaleOrderLine
        fields = [
            'id', 'product', 'product_sku', 'product_name',
            'qty', 'unit_price',
            'discount_type', 'discount_value',
            'discount', 'subtotal',
            'taxes', 'taxes_display',
            'amount_tax', 'amount_total'
        ]

    def get_taxes_display(self, obj):
        return [{'id': t.id, 'name': t.name, 'amount': t.amount} for t in obj.taxes.all()]


class SaleOrderLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleOrderLine
        fields = ['product', 'qty', 'unit_price', 'discount_type', 'discount_value', 'taxes']


class SaleOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines = SaleOrderLineSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_qty = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)
    invoice_numbers = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SaleOrder
        fields = [
            'id', 'number', 'customer', 'customer_name',
            'warehouse', 'warehouse_name',
            'status', 'status_display', 'date',
            'lines', 'subtotal', 'amount_tax', 'total', 'total_qty',
            'invoice_ids', 'invoice_numbers',
            'notes',
            'created_by', 'created_by_username', 'created_at',
            'confirmed_at', 'delivered_at', 'invoiced_at'
        ]
        read_only_fields = [
            'created_by', 'created_at', 'confirmed_at',
            'delivered_at', 'invoiced_at'
        ]
    
    def get_invoice_numbers(self, obj):
        return [inv.number for inv in obj.invoice_ids.all()]


class SaleOrderCreateSerializer(serializers.ModelSerializer):
    lines = SaleOrderLineCreateSerializer(many=True)
    account_revenue = serializers.IntegerField(required=False, write_only=False)
    account_receivable = serializers.IntegerField(required=False, write_only=False)

    class Meta:
        model = SaleOrder
        fields = [
            'customer', 'warehouse', 'date', 'notes',
            'lines', 'account_revenue', 'account_receivable'
        ]

    def validate(self, data):
        customer = data.get('customer')
        if customer and not customer.is_customer:
            raise serializers.ValidationError({
                'customer': 'El cliente debe tener is_customer=True.'
            })

        lines = data.get('lines', [])
        if not lines:
            raise serializers.ValidationError({
                'lines': 'Debe tener al menos una linea.'
            })

        return data

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        order = SaleOrder.objects.create(**validated_data)
        
        for line_data in lines_data:
            product = line_data.get('product')
            if product and not line_data.get('taxes'):
                line_data['taxes'] = list(product.template.sale_tax_ids.all())
            SaleOrderLine.objects.create(order=order, **line_data)
        
        return order


class SaleOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SaleOrder
        fields = ['id', 'number', 'customer_name', 'status', 'status_display', 'date', 'total']


class SaleQuoteLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    taxes_display = serializers.SerializerMethodField()

    class Meta:
        model = SaleQuoteLine
        fields = [
            'id', 'product', 'product_sku', 'product_name',
            'qty', 'unit_price',
            'discount_type', 'discount_value',
            'discount', 'subtotal',
            'taxes', 'taxes_display',
            'amount_tax', 'amount_total'
        ]

    def get_taxes_display(self, obj):
        return [{'id': t.id, 'name': t.name, 'amount': t.amount} for t in obj.taxes.all()]


class SaleQuoteLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleQuoteLine
        fields = ['product', 'qty', 'unit_price', 'discount_type', 'discount_value', 'taxes']


class SaleQuoteSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines = SaleQuoteLineSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    sale_order_number = serializers.CharField(source='sale_order.number', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SaleQuote
        fields = [
            'id', 'number', 'customer', 'customer_name',
            'warehouse', 'warehouse_name',
            'status', 'status_display', 'date', 'valid_until',
            'is_valid', 'lines', 'subtotal', 'amount_tax', 'total',
            'sale_order', 'sale_order_number',
            'notes',
            'created_by', 'created_by_username', 'created_at', 'accepted_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'accepted_at', 'sale_order']


class SaleQuoteCreateSerializer(serializers.ModelSerializer):
    lines = SaleQuoteLineCreateSerializer(many=True)
    account_revenue = serializers.IntegerField(required=False, write_only=False)
    account_receivable = serializers.IntegerField(required=False, write_only=False)

    class Meta:
        model = SaleQuote
        fields = [
            'customer', 'warehouse', 'date', 'valid_until', 'notes',
            'lines', 'account_revenue', 'account_receivable'
        ]

    def validate(self, data):
        customer = data.get('customer')
        if customer and not customer.is_customer:
            raise serializers.ValidationError({
                'customer': 'El cliente debe tener is_customer=True.'
            })

        lines = data.get('lines', [])
        if not lines:
            raise serializers.ValidationError({
                'lines': 'Debe tener al menos una linea.'
            })

        valid_until = data.get('valid_until')
        date = data.get('date')
        if valid_until and date and valid_until < date:
            raise serializers.ValidationError({
                'valid_until': 'La fecha de validez debe ser mayor o igual a la fecha del presupuesto.'
            })

        return data

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        quote = SaleQuote.objects.create(**validated_data)
        
        for line_data in lines_data:
            product = line_data.get('product')
            if product and not line_data.get('taxes'):
                line_data['taxes'] = list(product.template.sale_tax_ids.all())
            SaleQuoteLine.objects.create(quote=quote, **line_data)
        
        return quote


class SaleQuoteListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = SaleQuote
        fields = ['id', 'number', 'customer_name', 'status', 'status_display', 'date', 'valid_until', 'is_valid', 'total']
from rest_framework import serializers
from .models import Payment, PaymentLine, Check, CheckOperation


class PaymentLineSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    
    class Meta:
        model = PaymentLine
        fields = ['id', 'invoice', 'invoice_number', 'amount', 'reconciled']


class PaymentSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    journal_name = serializers.CharField(source='journal.description', read_only=True)
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    lines = PaymentLineSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'date', 'partner', 'partner_name',
            'journal', 'journal_name',
            'payment_type', 'payment_type_display',
            'method_type', 'method_type_display',
            'amount', 'currency', 'reference',
            'related_check', 'lines',
            'state', 'state_display',
            'created_by', 'created_by_username', 'created_at',
            'collected_at', 'reconciled_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'collected_at', 'reconciled_at']


class PaymentCreateSerializer(serializers.ModelSerializer):
    lines = PaymentLineSerializer(many=True, required=False)
    
    class Meta:
        model = Payment
        fields = [
            'date', 'partner', 'journal',
            'payment_type', 'method_type',
            'amount', 'currency', 'reference',
            'related_check', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        payment = Payment.objects.create(**validated_data)
        for line_data in lines_data:
            PaymentLine.objects.create(payment=payment, **line_data)
        return payment


class CheckOperationSerializer(serializers.ModelSerializer):
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    
    class Meta:
        model = CheckOperation
        fields = ['id', 'operation_type', 'operation_type_display', 'date', 'partner', 'partner_name', 'notes']


class CheckSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    check_type_display = serializers.CharField(source='get_check_type_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    operations = CheckOperationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Check
        fields = [
            'id', 'number', 'check_type', 'check_type_display',
            'partner', 'partner_name', 'bank', 'bank_name',
            'issue_date', 'expiration_date',
            'amount', 'currency', 'check_holder_vat',
            'source_sale', 'source_partner',
            'dest_partner', 'dest_purchase',
            'state', 'state_display',
            'created_at', 'operations'
        ]
        read_only_fields = ['created_at']


class CheckCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Check
        fields = [
            'number', 'check_type',
            'partner', 'bank',
            'issue_date', 'expiration_date',
            'amount', 'currency', 'check_holder_vat',
            'source_sale', 'source_partner'
        ]
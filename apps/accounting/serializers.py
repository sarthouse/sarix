from rest_framework import serializers
from .models import DocumentType, Journal, JournalLine


class DocumentTypeSerializer(serializers.ModelSerializer):
    document_class_display = serializers.CharField(source='get_document_class_display', read_only=True)
    iva_type_display = serializers.CharField(source='get_iva_type_display', read_only=True)

    class Meta:
        model = DocumentType
        fields = ['id', 'code', 'name', 'document_class', 'document_class_display', 'iva_type', 'iva_type_display', 'prefix', 'next_number', 'is_active']


class JournalLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    company_currency = serializers.SerializerMethodField()

    class Meta:
        model = JournalLine
        fields = [
            'id', 'account', 'account_code', 'account_name', 'description',
            'debit_amount', 'credit_amount', 'order',
            'currency', 'currency_code',
            'currency_debit_amount', 'currency_credit_amount',
            'exchange_rate', 'company_currency'
        ]
    
    def get_company_currency(self, obj):
        if obj.journal and obj.journal.period and obj.journal.period.company:
            return obj.journal.period.company.currency_id.code if obj.journal.period.company.currency_id else None
        return None


class JournalLineCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear líneas sin campos de lectura"""
    
    class Meta:
        model = JournalLine
        fields = [
            'account', 'description',
            'debit_amount', 'credit_amount', 'order',
            'currency',
            'currency_debit_amount', 'currency_credit_amount',
            'exchange_rate'
        ]


class JournalSerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    journal_type_display = serializers.CharField(source='get_journal_type_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    company_name = serializers.CharField(source='period.company.name', read_only=True)

    class Meta:
        model = Journal
        fields = [
            'id', 'number', 'date', 'description', 'status', 'status_display',
            'journal_type', 'journal_type_display', 'journal_code',
            'currency', 'currency_code', 'default_account',
            'period', 'company_name', 'reference', 'partner',
            'created_by_name', 'created_at', 'posted_at', 'lines'
        ]
    
    def validate(self, data):
        lines = data.get('lines', [])
        if len(lines) < 2:
            raise serializers.ValidationError("Un diario debe tener al menos dos líneas.")
        
        # Validar balance en moneda empresa
        total_debit = sum(l.get('debit_amount', 0) for l in lines)
        total_credit = sum(l.get('credit_amount', 0) for l in lines)
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f"El diario no está balanceado. Total Débito: {total_debit}, Total Crédito: {total_credit}"
            )
        
        # Validar balance en moneda de línea si existe
        currency_lines = [l for l in lines if l.get('currency')]
        if currency_lines:
            total_currency_debit = sum(l.get('currency_debit_amount', 0) or 0 for l in currency_lines)
            total_currency_credit = sum(l.get('currency_credit_amount', 0) or 0 for l in currency_lines)
            if total_currency_debit != total_currency_credit:
                raise serializers.ValidationError(
                    f"El diario no está balanceado en moneda extranjera. "
                    f"Total Débito: {total_currency_debit}, Total Crédito: {total_currency_credit}"
                )
        
        return data
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        journal = Journal.objects.create(**validated_data)
        for i, line_data in enumerate(lines_data):
            JournalLine.objects.create(journal=journal, order=i, **line_data)
        return journal
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', [])
        
        # Actualizar campos del journal
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar líneas
        if lines_data:
            instance.lines.all().delete()
            for i, line_data in enumerate(lines_data):
                JournalLine.objects.create(journal=instance, order=i, **line_data)
        
        return instance


class JournalListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    journal_type_display = serializers.CharField(source='get_journal_type_display', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    company_name = serializers.CharField(source='period.company.name', read_only=True)

    class Meta:
        model = Journal
        fields = [
            'id', 'number', 'date', 'description', 'status', 'status_display',
            'journal_type', 'journal_type_display', 'journal_code',
            'currency_code', 'company_name', 'reference'
        ]
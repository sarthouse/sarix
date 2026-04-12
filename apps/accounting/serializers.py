from rest_framework import serializers
from .models import Journal, JournalLine

class JournalLineSerializer(serializers.ModelSerializer):
    acount_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalLine
        fields = ['id', 'account', 'acount_code', 'account_name', 'description', 'debit_amount', 'credit_amount', 'order']
    
class JournalSerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Journal
        fields = ['id', 'number', 'date', 'description', 'status', 'status_display', 'period', 'reference', 'partner', 'created_by_name', 'created_at', 'posted_at', 'lines']
    
    def validate(self, data):
        lines = data.get('lines', [])
        if len(lines) < 2:
            raise serializers.ValidationError("Un diario debe tener al menos dos líneas.")
        total_debit = sum(l.get('debit_amount', 0) for l in lines)
        total_credit = sum(l.get('credit_amount', 0) for l in lines)
        if total_debit != total_credit:
            raise serializers.ValidationError(f"El diario no está balanceado. Total Débito: {total_debit}, Total Crédito: {total_credit}")
        return data
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        journal = Journal.objects.create(**validated_data)
        for i, line_data in enumerate(lines_data):
            JournalLine.objects.create(journal=journal, order=i, **line_data)
        return journal
    
class JournalListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Journal
        fields = ['id', 'number', 'date', 'description', 'status', 'status_display', 'created_by_name', 'reference']
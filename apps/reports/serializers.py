from rest_framework import serializers
from .models import CostCenter, FixedExpense, CashFlowCategory, CashFlowLine

class BalanceSheetSerializer(serializers.Serializer):
    assets = serializers.ListField()
    liabilities = serializers.ListField()
    equity = serializers.ListField()
    date = serializers.CharField(allow_null=True)
    total_assets = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_liabilities = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_equity = serializers.DecimalField(max_digits=18, decimal_places=2)

class ProfitLossSerializer(serializers.Serializer):
    revenues = serializers.ListField()
    expenses = serializers.ListField()
    total_revenue = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=18, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=18, decimal_places=2)
    
class GeneralLedgerSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    entries = serializers.ListField()


class CostCenterSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = CostCenter
        fields = ['id', 'name', 'code', 'description', 'parent', 'account', 'is_active', 'company', 'children']
    
    def get_children(self, obj):
        return [CostCenterSerializer(c).data for c in obj.children.all()]


class CostCenterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = ['name', 'code', 'description', 'parent', 'account', 'is_active', 'company']


class AllocationSerializer(serializers.Serializer):
    cost_center = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class FixedExpenseSerializer(serializers.ModelSerializer):
    allocations = AllocationSerializer(many=True, read_only=True)
    category_display = serializers.CharField(source='get_category_display')
    frequency_display = serializers.CharField(source='get_frequency_display')
    
    class Meta:
        model = FixedExpense
        fields = ['id', 'name', 'account', 'amount', 'frequency', 'frequency_display', 'start_date', 'end_date', 'category', 'category_display', 'is_active', 'company', 'allocations']


class FixedExpenseCreateSerializer(serializers.ModelSerializer):
    allocations = AllocationSerializer(many=True, required=False)
    
    class Meta:
        model = FixedExpense
        fields = ['name', 'account', 'amount', 'frequency', 'start_date', 'end_date', 'category', 'is_active', 'company', 'allocations']
    
    def create(self, validated_data):
        from .models import CostAllocation
        allocations_data = validated_data.pop('allocations', [])
        expense = FixedExpense.objects.create(**validated_data)
        for alloc in allocations_data:
            CostAllocation.objects.create(expense=expense, **alloc)
        return expense


class CashFlowCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CashFlowCategory
        fields = ['id', 'name', 'category_type', 'account_ids', 'company']


class CashFlowLineSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.name', read_only=True)
    
    class Meta:
        model = CashFlowLine
        fields = ['id', 'date', 'amount', 'flow_type', 'description', 'partner', 'partner_name', 'source_type', 'source_id', 'is_actual', 'category', 'category_name', 'cost_center', 'cost_center_name', 'company']
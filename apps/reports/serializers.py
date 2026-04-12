from rest_framework import serializers

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
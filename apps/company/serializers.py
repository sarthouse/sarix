from rest_framework import serializers
from .models import Company, CompanyConfig

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyConfigSerializer(serializers.ModelSerializer):
    account_cash_name = serializers.CharField(source='account_cash.name', read_only=True, allow_null=True)
    account_bank_name = serializers.CharField(source='account_bank.name', read_only=True, allow_null=True)
    account_values_in_portfolio_name = serializers.CharField(source='account_values_in_portfolio.name', read_only=True, allow_null=True)
    account_checks_rejected_name = serializers.CharField(source='account_checks_rejected.name', read_only=True, allow_null=True)
    account_third_party_checks_name = serializers.CharField(source='account_third_party_checks.name', read_only=True, allow_null=True)
    account_values_to_deposit_name = serializers.CharField(source='account_values_to_deposit.name', read_only=True, allow_null=True)
    default_perception_account_name = serializers.CharField(source='default_perception_account.name', read_only=True, allow_null=True)
    default_withholding_account_name = serializers.CharField(source='default_withholding_account.name', read_only=True, allow_null=True)
    perception_journal_name = serializers.CharField(source='perception_journal.description', read_only=True, allow_null=True)
    
    class Meta:
        model = CompanyConfig
        fields = [
            'company', 
            'account_asset', 'account_stock_valuation', 'account_cogs', 'account_revenue',
            'account_receivable', 'account_payable',
            'account_cash', 'account_cash_name', 'account_bank', 'account_bank_name',
            'account_values_in_portfolio', 'account_values_in_portfolio_name',
            'account_checks_rejected', 'account_checks_rejected_name',
            'account_third_party_checks', 'account_third_party_checks_name',
            'account_values_to_deposit', 'account_values_to_deposit_name',
            'account_cash_diff_income', 'account_cash_diff_expense',
            'account_exchange_gain', 'account_exchange_loss',
            'account_journal_suspense',
            'default_income_account', 'default_expense_account',
            'default_perception_account', 'default_perception_account_name',
            'default_withholding_account', 'default_withholding_account_name',
            'perception_journal', 'perception_journal_name'
        ]
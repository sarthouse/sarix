from rest_framework import serializers
from .models import Tax


class TaxSerializer(serializers.ModelSerializer):
    amount_type_display = serializers.CharField(source='get_amount_type_display', read_only=True)
    type_tax_use_display = serializers.CharField(source='get_type_tax_use_display', read_only=True)
    tax_scope_display = serializers.CharField(source='get_tax_scope_display', read_only=True)
    tax_group_display = serializers.CharField(source='get_tax_group_display', read_only=True)
    tax_type_display = serializers.CharField(source='get_tax_type_display', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    withholding_account_code = serializers.CharField(source='withholding_account.code', read_only=True, allow_null=True)

    class Meta:
        model = Tax
        fields = [
            'id', 'name', 'description', 'amount', 'amount_type', 'amount_type_display',
            'type_tax_use', 'type_tax_use_display', 'tax_scope', 'tax_scope_display',
            'tax_group', 'tax_group_display', 'include_base_amount', 'price_include',
            'is_base_affected', 'account', 'account_code', 'account_name',
            'children_taxes', 'sequence', 'is_active',
            'tax_type', 'tax_type_display', 'perception_base', 'apply_to',
            'is_withholding', 'withholding_account', 'withholding_account_code'
        ]


class TaxListSerializer(serializers.ModelSerializer):
    amount_type_display = serializers.CharField(source='get_amount_type_display', read_only=True)
    type_tax_use_display = serializers.CharField(source='get_type_tax_use_display', read_only=True)
    tax_group_display = serializers.CharField(source='get_tax_group_display', read_only=True)

    class Meta:
        model = Tax
        fields = ['id', 'name', 'amount', 'amount_type_display', 'type_tax_use_display', 'tax_group_display', 'is_active']
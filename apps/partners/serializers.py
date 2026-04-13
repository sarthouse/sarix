from rest_framework import serializers
from .models import Partner, PartnerCategory


class PartnerCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = PartnerCategory
        fields = ['id', 'name', 'color', 'parent', 'parent_name', 'shortcut', 'children_count']

    def get_children_count(self, obj):
        return obj.children.count()


class PartnerCategoryListSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartnerCategory
        fields = ['id', 'name', 'color', 'shortcut']


class PartnerSerializer(serializers.ModelSerializer):
    partner_type_display = serializers.CharField(source="get_partner_type_display", read_only=True)
    iva_condition_display = serializers.CharField(source="get_iva_condition_display", read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    category_names = serializers.SerializerMethodField()

    class Meta:
        model = Partner
        fields = [
            "id", "name", "partner_type", "partner_type_display",
            "email", "phone", "address", "is_active",
            "is_company", "parent", "parent_name",
            "category", "category_names",
            "street", "street2", "city", "state", "state_name",
            "country", "country_name", "postal_code",
            "cuit", "iva_condition", "iva_condition_display",
            "default_document_type", "default_account", "notes"
        ]

    def get_category_names(self, obj):
        return list(obj.category.values_list('name', flat=True))


class PartnerListSerializer(serializers.ModelSerializer):
    iva_condition_display = serializers.CharField(source="get_iva_condition_display", read_only=True)
    category_names = serializers.SerializerMethodField()

    class Meta:
        model = Partner
        fields = [
            "id", "name", "cuit", "partner_type", "iva_condition", "iva_condition_display",
            "is_company", "is_customer", "is_supplier", "is_active", "category_names"
        ]

    def get_category_names(self, obj):
        return list(obj.category.values_list('name', flat=True))
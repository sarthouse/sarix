from rest_framework import serializers
from .models import Partner

class PartnerSerializer(serializers.ModelSerializer):
    partner_type_display = serializers.CharField(source="get_partner_type_display", read_only=True)
    
    class Meta:
        model = Partner
        fields = [
            "id", "name", "cuit", "partner_type", "partner_type_display",
            "email", "phone", "address", "is_active", "default_account", "notes"
        ]

class PartnerListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Partner
        fields = ["id", "name", "cuit", "partner_type", "is_active"]
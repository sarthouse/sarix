from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    level = serializers.IntegerField(read_only=True)

    class Meta:
        model = Account
        fields = '__all__'

class AccountTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'account_type', 'allows_movements', 'children']

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField())) # Hint para Spectacular
    def get_children(self, obj):
        children = obj.get_children().filter(is_active=True)
        # Es vital usar self.__class__ o referenciar la clase para que no explote
        return self.__class__(children, many=True).data

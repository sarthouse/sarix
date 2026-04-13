from rest_framework import serializers
from .models import Country, State, Currency, CurrencyRate


class CountrySerializer(serializers.ModelSerializer):
    states_count = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'code_alpha3', 'numeric_code', 'is_active', 'states_count']

    def get_states_count(self, obj):
        return obj.states.count()


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model = State
        fields = ['id', 'name', 'code', 'country', 'country_name', 'is_active']


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ['id', 'currency', 'rate', 'date', 'company']


class CurrencySerializer(serializers.ModelSerializer):
    rates = CurrencyRateSerializer(many=True, read_only=True)

    class Meta:
        model = Currency
        fields = ['id', 'name', 'code', 'symbol', 'decimal_places', 'position', 'is_active', 'is_company_currency', 'rates']
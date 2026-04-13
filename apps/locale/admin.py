from django.contrib import admin
from .models import Country, State, Currency, CurrencyRate


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'code_alpha3', 'numeric_code', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['is_active']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country', 'is_active']
    list_filter = ['country', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'symbol', 'decimal_places', 'is_company_currency', 'is_active']
    list_filter = ['is_active', 'is_company_currency']
    search_fields = ['name', 'code', 'symbol']


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ['currency', 'rate', 'date', 'company']
    list_filter = ['currency', 'date']
    date_hierarchy = 'date'
from django.contrib import admin
from .models import Company, CompanyConfig

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuit', 'street', 'city', 'state', 'country', 'email', 'phone')
    search_fields = ('name', 'cuit')


@admin.register(CompanyConfig)
class CompanyConfigAdmin(admin.ModelAdmin):
    list_display = ('company', 'account_asset', 'account_cogs', 'account_revenue')
    search_fields = ('company__name',)
    fieldsets = (
        ('Empresa', {'fields': ('company',)}),
        ('Cuentas de Inventario', {'fields': ('account_asset', 'account_cogs')}),
        ('Cuentas de Ventas', {'fields': ('account_revenue', 'account_receivable', 'account_payable')}),
    )
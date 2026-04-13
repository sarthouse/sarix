from django.contrib import admin
from .models import Partner, PartnerCategory


@admin.register(PartnerCategory)
class PartnerCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'parent', 'shortcut']
    list_filter = ['parent']
    search_fields = ['name', 'shortcut']


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "cuit", "partner_type", "is_company", "iva_condition", "is_active"]
    list_filter = ["partner_type", "is_company", "iva_condition", "is_customer", "is_supplier", "is_active"]
    search_fields = ["name", "cuit", "email", "phone"]
    filter_horizontal = ['category']
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'partner_type', 'is_company', 'parent', 'email', 'phone', 'is_active')
        }),
        ('Dirección', {
            'fields': ('street', 'street2', 'city', 'state', 'country', 'postal_code')
        }),
        ('Datos Fiscales', {
            'fields': ('cuit', 'iva_condition', 'default_document_type', 'default_account')
        }),
        ('Clasificación', {
            'fields': ('is_customer', 'is_supplier', 'category')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
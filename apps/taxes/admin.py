from django.contrib import admin
from .models import Tax


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount', 'amount_type', 'type_tax_use', 'tax_group', 'is_active']
    list_filter = ['type_tax_use', 'tax_group', 'amount_type', 'is_active']
    search_fields = ['name']
    ordering = ['sequence', 'name']
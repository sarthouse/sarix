from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuit', 'fiscal_address', 'email', 'phone')
    search_fields = ('name', 'cuit')
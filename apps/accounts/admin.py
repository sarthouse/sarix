from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Account

@admin.register(Account)
class AccountAdmin(MPTTModelAdmin):
    list_display = ['code', 'name', 'account_type', 'is_active', 'allows_movements']
    list_filter = ['account_type', 'is_active', 'allows_movements']
    search_fields = ['code', 'name']
    mptt_level_indent = 20
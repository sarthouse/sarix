from django.contrib import admin
from .models import DocumentType, Journal, JournalLine


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'document_class', 'iva_type', 'prefix', 'next_number', 'is_active']
    list_filter = ['document_class', 'iva_type', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['number', 'date', 'description', 'status', 'period', 'reference']
    list_filter = ['status', 'period']
    search_fields = ['number', 'description', 'reference']
    inlines = [JournalLineInline]
    readonly_fields = ['created_by', 'created_at', 'posted_at']

@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ['journal', 'account', 'debit_amount', 'credit_amount', 'order']
    list_filter = ['account']
    search_fields = ['journal__number', 'account__code','account__name', 'description']
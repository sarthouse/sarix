from django.contrib import admin
from .models import (
    CostCenter, CostCenterDistribution, 
    FixedExpense, CostAllocation,
    CashFlowCategory, CashFlowLine
)


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'account', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['code', 'name']
    ordering = ['code']


@admin.register(CostCenterDistribution)
class CostCenterDistributionAdmin(admin.ModelAdmin):
    list_display = ['journal_line', 'cost_center', 'percentage']
    list_filter = ['cost_center']


@admin.register(FixedExpense)
class FixedExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'amount', 'frequency', 'is_active']
    list_filter = ['category', 'frequency', 'is_active', 'company']
    search_fields = ['name']
    ordering = ['name']


@admin.register(CostAllocation)
class CostAllocationAdmin(admin.ModelAdmin):
    list_display = ['expense', 'cost_center', 'percentage']
    list_filter = ['cost_center']


@admin.register(CashFlowCategory)
class CashFlowCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type']
    list_filter = ['category_type', 'company']
    ordering = ['category_type', 'name']


@admin.register(CashFlowLine)
class CashFlowLineAdmin(admin.ModelAdmin):
    list_display = ['date', 'flow_type', 'amount', 'partner', 'category', 'is_actual']
    list_filter = ['flow_type', 'is_actual', 'category', 'company']
    search_fields = ['description']
    date_hierarchy = 'date'
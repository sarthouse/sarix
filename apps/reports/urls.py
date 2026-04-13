from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BalanceSheetView, ProfitLossView, GeneralLedgerView,
    InventoryMetricsView, InventoryValuationView, SalesSummaryView,
    CostCenterViewSet, FixedExpenseViewSet, CashFlowCategoryViewSet, CashFlowLineViewSet
)

router = DefaultRouter()
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
router.register(r'fixed-expenses', FixedExpenseViewSet, basename='fixed-expense')
router.register(r'cashflow-categories', CashFlowCategoryViewSet, basename='cashflow-category')
router.register(r'cashflow', CashFlowLineViewSet, basename='cashflow-line')

urlpatterns = [
    path("balance/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("profit-loss/", ProfitLossView.as_view(), name="profit-loss"),
    path("general-ledger/", GeneralLedgerView.as_view(), name="general-ledger"),
    path("inventory/metrics/", InventoryMetricsView.as_view(), name="inventory-metrics"),
    path("inventory/valuation/", InventoryValuationView.as_view(), name="inventory-valuation"),
    path("sales/summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("", include(router.urls)),
]
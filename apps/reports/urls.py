from django.urls import path
from .views import (
    BalanceSheetView, ProfitLossView, GeneralLedgerView,
    InventoryMetricsView, InventoryValuationView, SalesSummaryView
)

urlpatterns = [
    path("balance/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("profit-loss/", ProfitLossView.as_view(), name="profit-loss"),
    path("general-ledger/", GeneralLedgerView.as_view(), name="general-ledger"),
    path("inventory/metrics/", InventoryMetricsView.as_view(), name="inventory-metrics"),
    path("inventory/valuation/", InventoryValuationView.as_view(), name="inventory-valuation"),
    path("sales/summary/", SalesSummaryView.as_view(), name="sales-summary"),
]
from django.urls import path
from .views import BalanceSheetView, ProfitLossView, GeneralLedgerView

urlpatterns = [
    path("balance/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("profit-loss/", ProfitLossView.as_view(), name="profit-loss"),
    path("general-ledger/", GeneralLedgerView.as_view(), name="general-ledger"),
]
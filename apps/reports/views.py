from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from apps.accounts.models import Account, AccountType
from apps.accounting.models import JournalLine, JournalStatus
from .serializers import ProfitLossSerializer, BalanceSheetSerializer, GeneralLedgerSerializer

def _balances(account_ids, period_ids=None, up_to_date=None):
    qs = JournalLine.objects.filter(
        account_id__in=account_ids,
        journal__status=JournalStatus.POSTED
    )
    if period_ids:
        qs = qs.filter(journal__period_id__in=period_ids)
    if up_to_date:
        qs = qs.filter(journal__date__lte=up_to_date)
    return {
        b["account_id"]: b
        for b in qs.values("account_id").annotate(
            total_debit=Sum("debit_amount"),
            total_credit=Sum("credit_amount")
        )
    }
class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BalanceSheetSerializer

    def get(self, request):
        up_to_date = request.query_params.get("date")
        data = self.get_raw_data(up_to_date)
        return Response(data)
    
    @staticmethod
    def get_raw_data(up_to_date=None):
        accounts = Account.objects.filter(is_active=True, allows_movements=True) \
                                    .values("id", "code", "name", "account_type")
        bals = _balances([a["id"] for a in accounts], up_to_date=up_to_date)
        result = {"assets": [], "liabilities": [], "equity": [], "date": up_to_date}
        for a in accounts:
            b = bals.get(a["id"], {})
            d = b.get("total_debit") or 0
            c = b.get("total_credit") or 0
            net = (d - c) if a["account_type"] in (AccountType.ASSET, AccountType.EXPENSE) \
                          else (c - d)
            entry = {**a, "balance": net}
            if a["account_type"] == AccountType.ASSET:
                result["assets"].append(entry)
            elif a["account_type"] == AccountType.LIABILITY:
                result["liabilities"].append(entry)
            elif a["account_type"] == AccountType.EQUITY:
                result["equity"].append(entry)
        result["total_assets"] = sum(x["balance"] for x in result["assets"])
        result["total_liabilities"] = sum(x["balance"] for x in result["liabilities"])
        result["total_equity"] = sum(x["balance"] for x in result["equity"])
        return result
    
class ProfitLossView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfitLossSerializer
    
    def get(self, request):
        period_ids = request.query_params.getlist("period")
        accounts = Account.objects.filter(
            is_active=True, allows_movements=True,
            account_type__in=[AccountType.REVENUE, AccountType.EXPENSE]
        ).values("id", "code", "name", "account_type")
        bals = _balances([a["id"] for a in accounts], period_ids=period_ids)
        revenues, expenses = [], []
        for a in accounts:
            b = bals.get(a["id"], {})
            d = b.get("total_debit") or 0
            c = b.get("total_credit") or 0
            net = (c - d) if a["account_type"] == AccountType.REVENUE else (d - c)
            (revenues if a["account_type"] == AccountType.REVENUE else expenses).append({**a, "amount": net})
        total_rev = sum(r["amount"] for r in revenues)
        total_exp = sum(e["amount"] for e in expenses)
        return Response({
            "revenues": revenues,
            "expenses": expenses,
            "total_revenue": total_rev,
            "total_expense": total_exp,
            "net_income": total_rev - total_exp,
        })
class GeneralLedgerView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GeneralLedgerSerializer

    def get(self, request):
        account_id = request.query_params.get("account")
        period_ids = request.query_params.getlist("period")
        qs = JournalLine.objects.filter(
            account_id=account_id, journal__status=JournalStatus.POSTED
        ).select_related("journal")
        if period_ids:
            qs = qs.filter(journal__period_id__in=period_ids)
        qs = qs.order_by("journal__date", "journal__number")
        running = 0
        rows = []
        for line in qs:
            running += line.debit_amount - line.credit_amount
            rows.append({
                "date": line.journal.date,
                "journal": line.journal.number,
                "description": line.description or line.journal.description,
                "debit": line.debit_amount,
                "credit": line.credit_amount,
                "balance": running,
            })
        return Response({"account_id": account_id, "entries": rows})
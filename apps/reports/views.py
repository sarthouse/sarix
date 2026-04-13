from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from apps.accounts.models import Account, AccountType
from apps.accounting.models import JournalLine, JournalStatus
from apps.inventory.models import Stock, StockMovement, Product, Warehouse
from apps.sales.models import SaleOrder, SaleOrderLine, SaleOrderStatus
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


class InventoryMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        warehouse_id = request.query_params.get('warehouse')
        
        qs = Stock.objects.select_related('product', 'warehouse')
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        
        stocks = list(qs.values(
            'product__sku', 'product__name', 'warehouse__code',
            'qty_available', 'qty_reserved', 'qty_min'
        ))
        
        total_available = sum(s['qty_available'] for s in stocks)
        total_reserved = sum(s['qty_reserved'] for s in stocks)
        total_min = sum(s['qty_min'] for s in stocks)
        
        negative_stocks = [s for s in stocks if s['qty_available'] < 0]
        low_stocks = [s for s in stocks if s['qty_available'] > 0 and s['qty_available'] <= s['qty_min']]
        
        return Response({
            'total_available': total_available,
            'total_reserved': total_reserved,
            'reserved_percentage': (total_reserved / total_available * 100) if total_available > 0 else 0,
            'negative_count': len(negative_stocks),
            'low_stock_count': len(low_stocks),
            'negative_stocks': negative_stocks[:10],
            'low_stocks': low_stocks[:10],
        })


class InventoryValuationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        warehouse_id = request.query_params.get('warehouse')
        
        qs = Stock.objects.select_related('product')
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        
        total_value = 0
        products = []
        for stock in qs:
            value = stock.qty_available * stock.product.cost_price
            total_value += value
            products.append({
                'product_sku': stock.product.sku,
                'product_name': stock.product.name,
                'warehouse_code': stock.warehouse.code,
                'qty_available': stock.qty_available,
                'cost_price': stock.product.cost_price,
                'value': value,
            })
        
        return Response({
            'total_value': total_value,
            'products': products,
        })


class SalesSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import date
        from django.db.models import Count
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        period_id = request.query_params.get('period')
        
        qs = SaleOrder.objects.filter(status=SaleOrderStatus.INVOICED)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if period_id:
            qs = qs.filter(period_id=period_id)
        
        total_sales = qs.count()
        total_revenue = sum(o.subtotal for o in qs)
        
        by_customer = qs.values('customer__name').annotate(
            total=Sum('lines__qty')
        ).order_by('-total')[:10]
        
        by_product = SaleOrderLine.objects.filter(
            order__in=qs
        ).values('product__sku', 'product__name').annotate(
            qty_sold=Sum('qty'),
            total=Sum('subtotal')
        ).order_by('-total')[:10]
        
        return Response({
            'total_orders': total_sales,
            'total_revenue': total_revenue,
            'by_customer': list(by_customer),
            'by_product': list(by_product),
        })
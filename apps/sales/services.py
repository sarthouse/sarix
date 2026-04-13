from django.db import models
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounting.models import Journal, JournalLine
from apps.inventory.models import Stock, StockMovement, StockQuant, ProductTemplate, ProductType
from apps.inventory.services import CompanyConfigService, StockQuantService, StockService
from .models import SaleOrder, SaleOrderLine, SaleOrderStatus, SaleQuote, SaleQuoteLine


class SaleOrderService:
    """Servicio para ordenes de venta."""

    @classmethod
    @transaction.atomic
    def confirm(cls, order: SaleOrder):
        """Confirma una orden y reserva stock."""
        if order.status != SaleOrderStatus.DRAFT:
            raise ValidationError("Solo se pueden confirmar ordenes en borrador.")

        if not order.customer.is_customer:
            raise ValidationError("El cliente debe tener is_customer=True.")
        
        if order.customer.blocked:
            raise ValidationError(f"El cliente {order.customer.name} está bloqueado.")
        
        if order.warehouse.periods.filter(is_closed=True).exists():
            raise ValidationError("El período contable está cerrado.")

        for line in order.lines.select_related('product').all():
            product = line.product
            template = product.template
            
            if template.product_type == ProductType.SERVICIO:
                continue

            if template.track_variation and product:
                StockQuantService.reserve(product, order.warehouse, line.qty)
            else:
                stock, _ = Stock.objects.select_for_update().get_or_create(
                    template=template,
                    product=product,
                    warehouse=order.warehouse,
                    defaults={'qty_available': 0, 'qty_reserved': 0, 'qty_min': 0}
                )[0]

                available = stock.qty_available - stock.qty_reserved
                if available < line.qty:
                    raise ValidationError(
                        f"Stock insuficiente para {product.sku}. "
                        f"Disponible: {available}, requerido: {line.qty}"
                    )

                stock.qty_reserved = F('qty_reserved') + line.qty
                stock.save(update_fields=['qty_reserved'])

        order.status = SaleOrderStatus.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save(update_fields=['status', 'confirmed_at'])

    @classmethod
    @transaction.atomic
    def deliver(cls, order: SaleOrder, period_id: int):
        """Entrega una orden: crea movements de salida + Journal COGS."""
        from apps.periods.models import AccountingPeriod
        
        if order.status != SaleOrderStatus.CONFIRMED:
            raise ValidationError("Solo se pueden entregar ordenes confirmadas.")
        
        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValidationError("Período contable no encontrado.")
        
        if period.is_closed or period.fiscal_year.is_locked:
            raise ValidationError("El período contable está cerrado o el año fiscal está bloqueado.")

        for line in order.lines.select_related('product').all():
            product = line.product
            template = product.template
            
            if template.product_type == ProductType.SERVICIO:
                continue

            movement = StockMovement.objects.create(
                movement_type='salida',
                product=product,
                template=template,
                warehouse_src=order.warehouse,
                qty=line.qty,
                unit_cost=product.get_cost_price(),
                partner=order.customer,
                reference=order.number,
                status='draft',
            )

            try:
                from apps.inventory.services import StockMovementService
                StockMovementService.post(movement, period_id, {})
            except Exception as e:
                raise ValidationError(f"Error al crear movimiento: {e}")

            if template.track_variation and product:
                StockQuantService.release_reservation(product, order.warehouse, line.qty)
            else:
                stock = Stock.objects.select_for_update().filter(
                    template=template,
                    product=product,
                    warehouse=order.warehouse
                ).first()
                if stock:
                    stock.qty_reserved = F('qty_reserved') - line.qty
                    stock.save(update_fields=['qty_reserved'])

        order.status = SaleOrderStatus.DELIVERED
        order.delivered_at = timezone.now()
        order.save(update_fields=['status', 'delivered_at'])

    @classmethod
    @transaction.atomic
    def invoice(cls, order: SaleOrder, period_id: int, request_data: dict = None):
        """Factura una orden: crea Journal de ingresos."""
        from apps.periods.models import AccountingPeriod
        
        if order.status != SaleOrderStatus.DELIVERED:
            raise ValidationError("Solo se pueden facturar ordenes entregadas.")
        
        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValidationError("Período contable no encontrado.")
        
        if period.is_closed or period.fiscal_year.is_locked:
            raise ValidationError("El período contable está cerrado o el año fiscal está bloqueado.")

        account_data = request_data or {}
        cls._create_revenue_journal(order, period_id, account_data)

        order.status = SaleOrderStatus.INVOICED
        order.invoiced_at = timezone.now()
        order.save(update_fields=['status', 'invoiced_at'])

    @classmethod
    @transaction.atomic
    def cancel(cls, order: SaleOrder):
        """Cancela una orden y libera reserva."""
        if order.status not in [SaleOrderStatus.DRAFT, SaleOrderStatus.CONFIRMED]:
            raise ValidationError("Solo se pueden cancelar ordenes en borrador o confirmadas.")
        
        if order.invoice_ids.exists():
            raise ValidationError("No se puede cancelar una orden que ya tiene facturas.")

        if order.status == SaleOrderStatus.CONFIRMED:
            for line in order.lines.select_related('product').all():
                product = line.product
                
                if product.product_type == ProductType.SERVICIO:
                    continue

                try:
                    stock = Stock.objects.select_for_update().get(
                        product=product,
                        warehouse=order.warehouse
                    )
                    stock.qty_reserved = F('qty_reserved') - line.qty
                    stock.save(update_fields=['qty_reserved'])
                except Stock.DoesNotExist:
                    pass

        order.status = SaleOrderStatus.CANCELLED
        order.save(update_fields=['status'])

    @classmethod
    def _create_revenue_journal(cls, order: SaleOrder, period_id: int, request_data: dict):
        """Crea el journal de ingresos (cuenta por cobrar vs ventas + taxes)."""
        from apps.periods.models import AccountingPeriod

        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValidationError("Periodo contable no encontrado.")

        receivable_account = order.customer.default_account
        if not receivable_account:
            receivable_account = CompanyConfigService.resolve_account(
                'receivable', request_data
            )

        revenue_account = CompanyConfigService.resolve_account(
            'revenue', request_data
        )

        amount_untaxed = order.subtotal
        amount_tax = order.amount_tax
        amount_total = order.amount_total

        journal = Journal.objects.create(
            date=order.invoiced_at.date(),
            description=f"Venta {order.number} - {order.customer.name}",
            period=period,
            partner=order.customer,
            reference=order.number,
            status='draft',
        )

        line_order = 1

        JournalLine.objects.create(
            journal=journal,
            account=receivable_account,
            debit_amount=amount_total,
            credit_amount=0,
            order=line_order,
        )
        line_order += 1

        JournalLine.objects.create(
            journal=journal,
            account=revenue_account,
            debit_amount=0,
            credit_amount=amount_untaxed,
            order=line_order,
        )
        line_order += 1

        for line in order.lines.all():
            for tax in line.taxes.all():
                tax_amount = line.subtotal * (tax.amount / 100) if tax.amount_type == 'percent' else 0
                if tax_amount > 0 and tax.account:
                    JournalLine.objects.create(
                        journal=journal,
                        account=tax.account,
                        debit_amount=0,
                        credit_amount=tax_amount,
                        order=line_order,
                        description=f"{tax.name} - {line.product.sku}"
                    )
                    line_order += 1

        journal.post()
        order.invoice_ids.add(journal)
        order.save(update_fields=['invoiced_at'])

        return journal


class SaleJournalService:
    """Alias para compatibilidad."""
    pass


class PriceService:
    """Servicio para calculo de precios en ventas."""

    @classmethod
    def calculate_line(cls, product, qty, discount_type=None, discount_value=0):
        """Calcula precio con descuento para una linea."""
        unit_price = product.get_sale_price()

        discount = 0
        if discount_type == 'percentage':
            discount = (unit_price * qty) * (discount_value / 100)
        elif discount_type == 'fixed':
            discount = discount_value

        subtotal = (unit_price * qty) - discount

        return {
            'unit_price': unit_price,
            'discount': discount,
            'subtotal': subtotal,
        }


class SaleQuoteService:
    """Servicio para presupuestos."""

    @classmethod
    @transaction.atomic
    def accept(cls, quote):
        """Acepta un presupuesto y crea la orden de venta."""
        from .models import SaleQuoteStatus, SaleQuoteLine

        if quote.status != SaleQuoteStatus.BUDGET:
            raise ValidationError("Solo se pueden aceptar presupuestos en estado presupuesto.")

        if not quote.is_valid:
            raise ValidationError("El presupuesto ha vencido.")

        if not quote.customer.is_customer:
            raise ValidationError("El cliente debe tener is_customer=True.")

        order = SaleOrder.objects.create(
            customer=quote.customer,
            warehouse=quote.warehouse,
            date=quote.date,
            status=SaleOrderStatus.DRAFT,
            notes=quote.notes,
            created_by=quote.created_by,
        )

        for line in quote.lines.all():
            SaleOrderLine.objects.create(
                order=order,
                product=line.product,
                qty=line.qty,
                unit_price=line.unit_price,
                discount_type=line.discount_type,
                discount_value=line.discount_value,
            )

        quote.sale_order = order
        quote.status = SaleQuoteStatus.ACCEPTED
        quote.accepted_at = timezone.now()
        quote.save(update_fields=['sale_order', 'status', 'accepted_at'])

        return order

    @classmethod
    @transaction.atomic
    def reject(cls, quote):
        """Rechaza un presupuesto."""
        from .models import SaleQuoteStatus

        if quote.status != SaleQuoteStatus.BUDGET:
            raise ValidationError("Solo se pueden rechazar presupuestos en estado presupuesto.")

        quote.status = SaleQuoteStatus.REJECTED
        quote.save(update_fields=['status'])

    @classmethod
    def check_expired(cls):
        """Marca presupuestos vencidos."""
        from datetime import date
        from .models import SaleQuoteStatus

        expired = SaleQuote.objects.filter(
            status=SaleQuoteStatus.BUDGET,
            valid_until__lt=date.today()
        )
        for quote in expired:
            quote.status = SaleQuoteStatus.EXPIRED
            quote.save(update_fields=['status'])
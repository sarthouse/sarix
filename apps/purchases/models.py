from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = 'draft', 'Presupuesto'
    SENT = 'sent', 'Enviado'
    TO_APPROVE = 'to_approve', 'Por Aprobar'
    PURCHASE = 'purchase', 'Confirmado'
    DONE = 'done', 'Finalizado'
    CANCELLED = 'cancelled', 'Anulado'


class PurchaseOrder(models.Model):
    """Pedido de Compra / Request for Quotation - equivalente a purchase.order de Odoo"""
    name = models.CharField(max_length=20, unique=True, blank=True)
    prefix = models.CharField(max_length=5, default='PO')
    
    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        limit_choices_to={'is_supplier': True}
    )
    partner_ref = models.CharField(
        max_length=100, blank=True,
        help_text='Referencia del proveedor / número de pedido del proveedor'
    )
    
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    
    state = models.CharField(
        max_length=20,
        choices=PurchaseOrderStatus.choices,
        default=PurchaseOrderStatus.DRAFT
    )
    
    date_order = models.DateField(
        help_text='Fecha en que se creó o validó el presupuesto'
    )
    date_approve = models.DateField(
        null=True, blank=True,
        help_text='Fecha de confirmación del pedido'
    )
    date_planned = models.DateField(
        null=True, blank=True,
        help_text='Fecha esperada de entrega'
    )
    
    currency = models.ForeignKey(
        'locale.Currency',
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    
    origin = models.CharField(
        max_length=100, blank=True,
        help_text='Documento origen (MO, Sale Order, etc)'
    )
    
    notes = models.TextField(blank=True)
    
    picking_ids = models.ManyToManyField(
        'inventory.StockMovement',
        blank=True,
        related_name='purchase_orders',
        help_text='Recepciones vinculadas a este pedido'
    )
    
    invoice_ids = models.ManyToManyField(
        'accounting.Journal',
        blank=True,
        related_name='purchase_orders',
        help_text='Facturas de proveedor vinculadas a este pedido'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido de Compra'
        verbose_name_plural = 'Pedidos de Compra'
        ordering = ['-date_order', '-name']

    def __str__(self):
        return f"{self.name} - {self.partner.name}"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from django.db.models import Max
        year = self.date_order.year
        prefix_str = f"{self.prefix}-{year}-"
        last = PurchaseOrder.objects.filter(
            name__startswith=prefix_str
        ).aggregate(Max('name'))
        last_num = last.get('name__max', None)
        if last_num and last_num.startswith(prefix_str):
            seq = int(last_num.split('-')[-1]) + 1
        else:
            seq = 1
        return f"{prefix_str}{seq:06d}"

    @property
    def amount_untaxed(self):
        return sum(line.subtotal for line in self.lines.all())

    @property
    def amount_tax(self):
        total = 0
        for line in self.lines.all():
            for tax in line.taxes.all():
                total += line.subtotal * (tax.amount / 100)
        return total

    @property
    def amount_total(self):
        return self.amount_untaxed + self.amount_tax

    @property
    def invoiced_status(self):
        """Estado de facturación: no, to_invoice, invoiced, partial"""
        total_lines = sum(line.qty for line in self.lines.all())
        total_invoiced = sum(line.qty_invoiced for line in self.lines.all())
        
        if total_invoiced == 0:
            return 'no'
        elif total_invoiced >= total_lines:
            return 'invoiced'
        elif total_invoiced > 0:
            return 'partial'
        return 'no'

    @property
    def receipt_status(self):
        """Estado de recepción: no, to_receive, partially, received"""
        total_lines = sum(line.qty for line in self.lines.all())
        total_received = sum(line.qty_received for line in self.lines.all())
        
        if total_received == 0:
            return 'no'
        elif total_received >= total_lines:
            return 'received'
        elif total_received > 0:
            return 'partially'
        return 'no'

    def clean(self):
        if self.state == PurchaseOrderStatus.DRAFT:
            if not self.date_order:
                raise ValidationError("La fecha del pedido es requerida")

    def confirm(self):
        """Confirma el pedido - pasa a estado purchase"""
        from apps.periods.models import AccountingPeriod
        from django.utils import timezone
        
        if self.state not in [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SENT]:
            raise ValidationError("Solo se pueden confirmar pedidos en borrador o enviados")
        
        if not self.lines.exists():
            raise ValidationError("El pedido debe tener al menos una línea.")
        
        if self.warehouse.periods.filter(is_closed=True).exists():
            raise ValidationError("El período contable está cerrado.")
        
        self.state = PurchaseOrderStatus.PURCHASE
        self.date_approve = timezone.now().date()
        self.save()

    def cancel(self):
        """Cancela el pedido"""
        if self.state == PurchaseOrderStatus.DONE:
            raise ValidationError("No se puede cancelar un pedido finalizado")
        
        if self.invoice_ids.exists():
            raise ValidationError("No se puede cancelar un pedido que ya tiene facturas.")
        
        if self.picking_ids.exists():
            raise ValidationError("No se puede cancelar un pedido que tiene recepciones.")
        
        self.state = PurchaseOrderStatus.CANCELLED
        self.save()

    def draft(self):
        """Vuelve a borrador"""
        if self.state != PurchaseOrderStatus.CANCELLED:
            raise ValidationError("Solo se puede volver a borrador desde cancelado")
        
        self.state = PurchaseOrderStatus.DRAFT
        self.save()

    def action_restock(self):
        """Crea una recepción (StockMovement) vinculada al pedido"""
        from apps.inventory.models import StockMovement, Location, PickingType
        
        if self.state != PurchaseOrderStatus.PURCHASE:
            raise ValidationError("Solo se pueden crear recepciones de pedidos confirmados")
        
        movements = []
        
        for line in self.lines.all():
            if line.qty - line.qty_received > 0:
                qty_to_receive = line.qty - line.qty_received
                
                # Obtener picking type para receipt
                picking_type = PickingType.objects.filter(
                    warehouse=self.warehouse,
                    code='incoming'
                ).first()
                
                # Obtener locations por defecto
                location_src = Location.get_default_src(self.warehouse, 'incoming')
                location_dst = Location.get_default_dst(self.warehouse, 'incoming')
                
                movement = StockMovement.objects.create(
                    picking_type=picking_type,
                    movement_type='entrada',
                    product=line.product,
                    template=line.template,
                    qty=qty_to_receive,
                    unit_cost=line.price_unit,
                    location_src=location_src,
                    location_dst=location_dst,
                    origin=f"PO:{self.name}",
                    partner=self.partner,
                    created_by=self.created_by
                )
                movements.append(movement)
                
                # Vincular al pedido
                self.picking_ids.add(movement)
        
        return movements

    def action_create_invoice(self):
        """Crea una factura de proveedor (Vendor Bill)"""
        from apps.accounting.models import Journal, JournalLine
        from apps.accounting.models import JournalType
        
        if self.state != PurchaseOrderStatus.PURCHASE:
            raise ValidationError("Solo se pueden crear facturas de pedidos confirmados")
        
        # Buscar o crear journal de compras
        journal = Journal.objects.filter(
            journal_type=JournalType.PURCHASE,
            period__company=self.warehouse.company
        ).first()
        
        if not journal:
            raise ValidationError("No existe un diario de compras para la empresa")
        
        # Crear journal para la factura
        invoice_journal = Journal.objects.create(
            date=self.date_approve or timezone.now().date(),
            description=f"Factura de Proveedor - {self.name}",
            journal_type=JournalType.PURCHASE,
            journal_code=f"VIN-{self.partner.name[:3].upper()}",
            currency=self.currency,
            period=journal.period,
            partner=self.partner,
            created_by=self.created_by
        )
        
        # Buscar cuenta de proveedores
        from apps.accounts.models import Account
        account_payable = Account.objects.filter(
            code='2100',  # Proveedores
            company=self.warehouse.company
        ).first()
        
        total = 0
        line_order = 0
        
        for line in self.lines.all():
            # Cuenta de gasto/producto
            if line.template:
                account_expense = (
                    line.template.property_account_expense or
                    line.template.category.property_account_expense
                )
            else:
                account_expense = None
            
            if not account_expense:
                continue
            
            # Línea de movimiento (débito)
            JournalLine.objects.create(
                journal=invoice_journal,
                account=account_expense,
                description=f"{line.product.name if line.product else line.template.name} x {line.qty}",
                debit_amount=line.subtotal,
                order=line_order
            )
            line_order += 1
            
            # Impuesto (si aplica)
            for tax in line.taxes.all():
                tax_account = tax.account
                if tax_account:
                    tax_amount = line.subtotal * (tax.amount / 100)
                    JournalLine.objects.create(
                        journal=invoice_journal,
                        account=tax_account,
                        description=f"IVA - {line.product.name if line.product else line.template.name}",
                        debit_amount=tax_amount,
                        order=line_order
                    )
                    line_order += 1
            
            total += line.subtotal
        
        # Línea de contrapartida (crédito) - cuenta payable
        if account_payable:
            JournalLine.objects.create(
                journal=invoice_journal,
                account=account_payable,
                description=f"Proveedor: {self.partner.name}",
                credit_amount=invoice_journal.lines.aggregate(
                    total=models.Sum('debit_amount')
                )['total'] or 0,
                order=line_order
            )
        
        # Post journal y vincular al pedido
        invoice_journal.post()
        self.invoice_ids.add(invoice_journal)
        
        # Marcar líneas como facturadas
        for line in self.lines.all():
            line.qty_invoiced = line.qty
        
        return invoice_journal


class PurchaseOrderLine(models.Model):
    """Línea de pedido de compra - equivalente a purchase.order.line de Odoo"""
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    product = models.ForeignKey(
        'inventory.Product',
        null=True, blank=True,
        on_delete=models.PROTECT,
        help_text='Producto específico (variante)'
    )
    template = models.ForeignKey(
        'inventory.ProductTemplate',
        null=True, blank=True,
        on_delete=models.PROTECT,
        help_text='Producto genérico (plantilla)'
    )
    
    name = models.CharField(
        max_length=500,
        help_text='Descripción de la línea'
    )
    
    qty = models.DecimalField(
        max_digits=14, decimal_places=4,
        default=1,
        help_text='Cantidad ordenada'
    )
    price_unit = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Precio unitario'
    )
    
    taxes = models.ManyToManyField(
        'taxes.Tax',
        blank=True,
        related_name='purchase_order_lines',
        help_text='Impuestos aplicables'
    )
    
    date_planned = models.DateField(
        null=True, blank=True,
        help_text='Fecha esperada de entrega de esta línea'
    )
    
    qty_received = models.DecimalField(
        max_digits=14, decimal_places=4,
        default=0,
        help_text='Cantidad recibida'
    )
    qty_invoiced = models.DecimalField(
        max_digits=14, decimal_places=4,
        default=0,
        help_text='Cantidad facturada'
    )
    
    uom = models.ForeignKey(
        'inventory.UnitOfMeasure',
        null=True, blank=True,
        on_delete=models.PROTECT,
        help_text='Unidad de medida'
    )

    class Meta:
        verbose_name = 'Línea de Pedido de Compra'
        verbose_name_plural = 'Líneas de Pedido de Compra'
        ordering = ['order', 'id']

    def __str__(self):
        product_name = self.product.name if self.product else (self.template.name if self.template else 'N/A')
        return f"{self.order.name} - {product_name} x {self.qty}"

    def clean(self):
        if not self.product and not self.template:
            raise ValidationError("Debe especificar un producto")
        
        if not self.name:
            product_name = self.product.name if self.product else (self.template.name if self.template else '')
            self.name = product_name

    @property
    def subtotal(self):
        return (self.qty or 0) * (self.price_unit or 0)

    def save(self, *args, **kwargs):
        if not self.uom:
            if self.product:
                self.uom = self.product.template.unit_of_measure
            elif self.template:
                self.uom = self.template.unit_of_measure
        
        if not self.name:
            self.name = self.product.name if self.product else (self.template.name if self.template else '')
        
        super().save(*args, **kwargs)


class PurchaseOrderPartnerLine(models.Model):
    """Precios por proveedor en el producto - equivalente a product.supplierinfo de Odoo"""
    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.CASCADE,
        related_name='supplier_info',
        limit_choices_to={'is_supplier': True}
    )
    product_template = models.ForeignKey(
        'inventory.ProductTemplate',
        on_delete=models.CASCADE,
        related_name='supplier_info'
    )
    
    product_code = models.CharField(
        max_length=50, blank=True,
        help_text='Código del producto en el proveedor'
    )
    product_name = models.CharField(
        max_length=200, blank=True,
        help_text='Nombre del producto en el proveedor'
    )
    
    min_qty = models.DecimalField(
        max_digits=14, decimal_places=4,
        default=1,
        help_text='Cantidad mínima de compra'
    )
    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Precio unitario'
    )
    
    currency = models.ForeignKey(
        'locale.Currency',
        on_delete=models.PROTECT
    )
    
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Info. Proveedor'
        verbose_name_plural = 'Infos. de Proveedores'
        unique_together = ['partner', 'product_template']

    def __str__(self):
        return f"{self.partner.name} - {self.product_template.sku}"
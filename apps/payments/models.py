from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.core.validators import PaymentValidator, CheckValidator


class PaymentMethodType(models.TextChoices):
    CASH = 'cash', 'Efectivo'
    CHECK = 'check', 'Cheque'
    TRANSFER = 'transfer', 'Transferencia Bancaria'
    GIRO = 'giro', 'Giro'


class PaymentType(models.TextChoices):
    INBOUND = 'inbound', 'Cobro'
    OUTBOUND = 'outbound', 'Pago'


class PaymentState(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    POSTED = 'posted', 'Confirmado'
    COLLECTED = 'collected', 'Cobrado/Pagado'
    RECONCILED = 'reconciled', 'Conciliado'
    CANCELLED = 'anulado', 'Anulado'


class Payment(models.Model):
    date = models.DateField()
    partner = models.ForeignKey('partners.Partner', on_delete=models.PROTECT, related_name='payments')
    journal = models.ForeignKey('accounting.Journal', on_delete=models.PROTECT, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PaymentType.choices)
    method_type = models.CharField(max_length=20, choices=PaymentMethodType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey('locale.Currency', on_delete=models.PROTECT, related_name='payments')
    reference = models.CharField(max_length=100, blank=True, help_text='Número de comprobante o referencia')
    
    related_check = models.ForeignKey('payments.Check', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    state = models.CharField(max_length=20, choices=PaymentState.choices, default=PaymentState.DRAFT)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='payments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.partner.name} - {self.amount}"
    
    def clean(self):
        if self.partner.is_customer == False and self.partner.is_supplier == False:
            raise ValidationError("El partner debe ser cliente o proveedor.")
        if self.payment_type == PaymentType.INBOUND and not self.partner.is_customer:
            raise ValidationError("Para cobros, el partner debe ser cliente.")
        if self.payment_type == PaymentType.OUTBOUND and not self.partner.is_supplier:
            raise ValidationError("Para pagos, el partner debe ser proveedor.")


class PaymentLine(models.Model):
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name='lines')
    invoice = models.ForeignKey('accounting.Journal', on_delete=models.CASCADE, related_name='payment_lines')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reconciled = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Línea de Pago'
        verbose_name_plural = 'Líneas de Pago'
        unique_together = [['payment', 'invoice']]
    
    def __str__(self):
        return f"{self.payment.id} - {self.invoice.number} - {self.amount}"


class CheckState(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    HELD = 'held', 'En Cartera'
    DEPOSITED = 'deposited', 'Depositado'
    REJECTED = 'rejected', 'Rechazado'
    RECONCILED = 'reconciled', 'Conciliado'
    CANCELLED = 'anulado', 'Anulado'


class CheckType(models.TextChoices):
    THIRD_PARTY = 'third_party', 'Cheque de Terceros'
    OWN = 'own', 'Cheque Propio'
    DEFERRED = 'deferred', 'Cheque Diferido'


class Check(models.Model):
    number = models.CharField(max_length=20)
    check_type = models.CharField(max_length=20, choices=CheckType.choices)
    state = models.CharField(max_length=20, choices=CheckState.choices, default=CheckState.DRAFT)
    
    partner = models.ForeignKey('partners.Partner', on_delete=models.PROTECT, related_name='checks')
    bank = models.ForeignKey('partners.Partner', null=True, blank=True, on_delete=models.SET_NULL, related_name='checks_bank')
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey('locale.Currency', on_delete=models.PROTECT, related_name='checks')
    
    check_holder_vat = models.CharField(max_length=20, blank=True, help_text='CUIT del librador/firmante')
    
    source_sale = models.ForeignKey('sales.SaleOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='checks')
    source_partner = models.ForeignKey('partners.Partner', on_delete=models.SET_NULL, null=True, blank=True, related_name='checks_received')
    
    dest_partner = models.ForeignKey('partners.Partner', on_delete=models.SET_NULL, null=True, blank=True, related_name='checks_delivered')
    dest_purchase = models.ForeignKey('purchases.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='checks_delivered')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cheque'
        verbose_name_plural = 'Cheques'
    
    def __str__(self):
        return f"Cheque {self.number} - {self.partner.name} - {self.amount}"
    
    def clean(self):
        """Valida usando validador centralizado"""
        CheckValidator.validate(self)


class CheckOperationType(models.TextChoices):
    RECEIVE = 'receive', 'Recibido'
    DEPOSIT = 'deposit', 'Depositado'
    REJECT = 'reject', 'Rechazado'
    ENDORSE = 'endorse', 'Endosado'
    DELIVER = 'deliver', 'Entregado'
    CANCEL = 'cancel', 'Anulado'


class CheckOperation(models.Model):
    related_check = models.ForeignKey('Check', on_delete=models.CASCADE, related_name='operations')
    operation_type = models.CharField(max_length=20, choices=CheckOperationType.choices)
    date = models.DateTimeField(auto_now_add=True)
    partner = models.ForeignKey('partners.Partner', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['date']
        verbose_name = 'Operación de Cheque'
        verbose_name_plural = 'Operaciones de Cheques'
    
    def __str__(self):
        return f"{self.related_check.number} - {self.get_operation_type_display()}"
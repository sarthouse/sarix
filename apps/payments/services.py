from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounting.models import Journal, JournalLine, JournalStatus
from apps.company.models import CompanyConfig
from .models import Payment, Check, CheckOperation, PaymentState, CheckState, PaymentMethodType


class PaymentService:
    """Servicio para gestión de pagos y cobros"""
    
    @classmethod
    def confirm(cls, payment: Payment):
        """Confirma un pago"""
        if payment.state != PaymentState.DRAFT:
            raise ValidationError("Solo se pueden confirmar pagos en borrador.")
        
        payment.state = PaymentState.POSTED
        payment.save(update_fields=['state'])
    
    @classmethod
    @transaction.atomic
    def collect(cls, payment: Payment):
        """Marca como cobrado/pagado y crea asiento contable"""
        if payment.state != PaymentState.POSTED:
            raise ValidationError("El pago debe estar confirmado.")
        
        company = payment.journal.period.company
        config = CompanyConfig.get(company)
        
        # Determinar cuenta segun método de pago
        if payment.method_type == PaymentMethodType.CASH:
            account_dest = config.account_cash if config and config.account_cash else None
        elif payment.method_type == PaymentMethodType.TRANSFER:
            account_dest = payment.journal.default_account
        elif payment.method_type == PaymentMethodType.CHECK:
            if payment.related_check:
                if payment.related_check.check_type == 'own':
                    account_dest = config.account_values_in_portfolio if config else None
                else:
                    account_dest = config.account_third_party_checks if config else None
            else:
                account_dest = payment.journal.default_account
        else:
            account_dest = payment.journal.default_account
        
        if not account_dest:
            raise ValidationError("No se encontró cuenta contable para el método de pago.")
        
        # Crear asiento contable
        journal = cls._create_payment_journal(payment, account_dest)
        
        payment.state = PaymentState.COLLECTED
        payment.collected_at = timezone.now()
        payment.save(update_fields=['state', 'collected_at'])
        
        return journal
    
    @classmethod
    def _create_payment_journal(cls, payment: Payment, account_dest):
        """Crea el journal contable para el pago"""
        from apps.periods.models import AccountingPeriod
        from django.utils import timezone
        
        period = AccountingPeriod.objects.filter(
            company=payment.journal.period.company,
            start_date__lte=payment.date,
            end_date__gte=payment.date,
            is_closed=False
        ).first()
        
        if not period:
            raise ValidationError("No hay período contable abierto para la fecha del pago.")
        
        payment_account = payment.partner.default_account
        if not payment_account:
            raise ValidationError("El partner no tiene cuenta por defecto.")
        
        descripcion = f"{payment.get_payment_type_display()} {payment.partner.name}"
        if payment.reference:
            descripcion += f" - {payment.reference}"
        
        journal = Journal.objects.create(
            date=payment.date,
            description=descripcion,
            journal_type=payment.journal.journal_type,
            journal_code=payment.journal.journal_code,
            period=period,
            partner=payment.partner,
            reference=payment.reference or str(payment.id),
            status='draft',
            currency=payment.currency,
        )
        
        line_order = 1
        
        if payment.payment_type == 'inbound':
            # Cobro: Débito a banco/caja, Crédito a cliente
            JournalLine.objects.create(
                journal=journal,
                account=account_dest,
                debit_amount=payment.amount,
                credit_amount=0,
                order=line_order
            )
            line_order += 1
            JournalLine.objects.create(
                journal=journal,
                account=payment_account,
                debit_amount=0,
                credit_amount=payment.amount,
                order=line_order
            )
        else:
            # Pago: Débito a proveedor, Crédito a banco/caja
            JournalLine.objects.create(
                journal=journal,
                account=payment_account,
                debit_amount=payment.amount,
                credit_amount=0,
                order=line_order
            )
            line_order += 1
            JournalLine.objects.create(
                journal=journal,
                account=account_dest,
                debit_amount=0,
                credit_amount=payment.amount,
                order=line_order
            )
        
        journal.post()
        return journal
    
    @classmethod
    @transaction.atomic
    def reconcile(cls, payment: Payment):
        """Concilia el pago con las líneas de factura"""
        if payment.state != PaymentState.COLLECTED:
            raise ValidationError("El pago debe estar cobrado/pagado primero.")
        
        for line in payment.lines.all():
            if not line.reconciled:
                line.reconciled = True
                line.save(update_fields=['reconciled'])
        
        payment.state = PaymentState.RECONCILED
        payment.reconciled_at = timezone.now()
        payment.save(update_fields=['state', 'reconciled_at'])
    
    @classmethod
    def cancel(cls, payment: Payment):
        """Cancela un pago"""
        if payment.state == PaymentState.RECONCILED:
            raise ValidationError("No se puede cancelar un pago ya conciliado.")
        
        payment.state = PaymentState.CANCELLED
        payment.save(update_fields=['state'])
    
    @classmethod
    @transaction.atomic
    def deposit_check(cls, check: Check):
        """Deposita un cheque de terceros"""
        from apps.periods.models import AccountingPeriod
        from apps.company.models import CompanyConfig
        from apps.accounting.models import Journal, JournalLine
        
        if check.state != CheckState.HELD:
            raise ValidationError("El cheque debe estar en cartera para depositar.")
        
        company = check.source_partner.main_company if check.source_partner else None
        if not company:
            raise ValidationError("El partner no tiene empresa asignada.")
        
        config = CompanyConfig.get(company)
        if not config or not config.account_third_party_checks:
            raise ValidationError("No está configurada la cuenta de cheques de terceros.")
        
        if not config.account_values_to_deposit:
            raise ValidationError("No está configurada la cuenta de valores a depositar.")
        
        period = AccountingPeriod.objects.filter(
            company=company,
            start_date__lte=check.issue_date,
            end_date__gte=check.issue_date,
            is_closed=False
        ).first()
        
        if not period:
            raise ValidationError("No hay período contable abierto.")
        
        journal = Journal.objects.create(
            date=check.issue_date,
            description=f"Depósito Cheque {check.number}",
            journal_type='cash',
            journal_code='DEP',
            period=period,
            partner=check.partner,
            reference=check.number,
            status='draft',
            currency=check.currency,
        )
        
        # Débito: Valores a depositar
        # Crédito: Cheques de terceros
        JournalLine.objects.create(
            journal=journal,
            account=config.account_values_to_deposit,
            debit_amount=check.amount,
            credit_amount=0,
            order=1
        )
        JournalLine.objects.create(
            journal=journal,
            account=config.account_third_party_checks,
            debit_amount=0,
            credit_amount=check.amount,
            order=2
        )
        
        journal.post()
        
        check.state = CheckState.DEPOSITED
        check.save(update_fields=['state'])
        
        CheckOperation.objects.create(
            check=check,
            operation_type='deposit',
            partner=check.partner,
            notes=f"Depósito journal: {journal.number}"
        )
        
        return journal
    
    @classmethod
    @transaction.atomic
    def endorse_check(cls, check: Check, partner_id: int):
        """Endosa un cheque a un tercero"""
        from apps.periods.models import AccountingPeriod
        from apps.company.models import CompanyConfig
        from apps.partners.models import Partner
        
        if check.state != CheckState.HELD:
            raise ValidationError("El cheque debe estar en cartera para endosar.")
        
        partner = Partner.objects.get(id=partner_id)
        
        company = check.source_partner.main_company if check.source_partner else None
        config = CompanyConfig.get(company)
        
        period = AccountingPeriod.objects.filter(
            company=company,
            start_date__lte=check.issue_date,
            end_date__gte=check.issue_date,
            is_closed=False
        ).first()
        
        journal = Journal.objects.create(
            date=check.issue_date,
            description=f"Endoso Cheque {check.number} a {partner.name}",
            journal_type='cash',
            journal_code='END',
            period=period,
            partner=partner,
            reference=check.number,
            status='draft',
            currency=check.currency,
        )
        
        account_dest = partner.default_account or (config.account_third_party_checks if config else None)
        
        JournalLine.objects.create(
            journal=journal,
            account=account_dest,
            debit_amount=check.amount,
            credit_amount=0,
            order=1
        )
        JournalLine.objects.create(
            journal=journal,
            account=config.account_third_party_checks if config else None,
            debit_amount=0,
            credit_amount=check.amount,
            order=2
        )
        
        journal.post()
        
        check.state = CheckState.RECONCILED
        check.dest_partner = partner
        check.save(update_fields=['state', 'dest_partner'])
        
        CheckOperation.objects.create(
            check=check,
            operation_type='endorse',
            partner=partner,
            notes=f"Endosado a {partner.name} - Journal: {journal.number}"
        )
    
    @classmethod
    @transaction.atomic
    def reject_check(cls, check: Check):
        """Marca un cheque como rechazado"""
        from apps.periods.models import AccountingPeriod
        from apps.company.models import CompanyConfig
        from apps.accounting.models import Journal, JournalLine
        
        if check.state not in [CheckState.HELD, CheckState.DEPOSITED]:
            raise ValidationError("El cheque no puede ser rechazado en este estado.")
        
        company = check.source_partner.main_company if check.source_partner else None
        config = CompanyConfig.get(company)
        
        period = AccountingPeriod.objects.filter(
            company=company,
            start_date__lte=check.issue_date,
            end_date__gte=check.issue_date,
            is_closed=False
        ).first()
        
        journal = Journal.objects.create(
            date=timezone.now().date(),
            description=f"Cheque Rechazado {check.number}",
            journal_type='cash',
            journal_code='RECH',
            period=period,
            partner=check.partner,
            reference=check.number,
            status='draft',
            currency=check.currency,
        )
        
        # Débito: Cheques rechazados
        # Crédito: Cheques de terceros o Valores a depositar
        account_credit = config.account_values_to_deposit if check.state == CheckState.DEPOSITED else config.account_third_party_checks
        
        JournalLine.objects.create(
            journal=journal,
            account=config.account_checks_rejected if config else None,
            debit_amount=check.amount,
            credit_amount=0,
            order=1
        )
        JournalLine.objects.create(
            journal=journal,
            account=account_credit,
            debit_amount=0,
            credit_amount=check.amount,
            order=2
        )
        
        journal.post()
        
        check.state = CheckState.REJECTED
        check.save(update_fields=['state'])
        
        CheckOperation.objects.create(
            check=check,
            operation_type='reject',
            notes=f"Cheque rechado - Journal: {journal.number}"
        )
    
    @classmethod
    @transaction.atomic
    def deliver_check(cls, check: Check, partner_id: int):
        """Entrega un cheque propio a un proveedor"""
        from apps.periods.models import AccountingPeriod
        from apps.company.models import CompanyConfig
        from apps.partners.models import Partner
        from apps.accounting.models import Journal, JournalLine
        
        if check.check_type != 'own':
            raise ValidationError("Solo se pueden entregar cheques propios.")
        
        if check.state != CheckState.HELD:
            raise ValidationError("El cheque debe estar en cartera.")
        
        partner = Partner.objects.get(id=partner_id)
        
        company = check.dest_partner.main_company if check.dest_partner else None
        config = CompanyConfig.get(company)
        
        period = AccountingPeriod.objects.filter(
            company=company,
            start_date__lte=check.issue_date,
            end_date__gte=check.issue_date,
            is_closed=False
        ).first()
        
        journal = Journal.objects.create(
            date=check.issue_date,
            description=f"Pago con Cheque {check.number} a {partner.name}",
            journal_type='cash',
            journal_code='PCH',
            period=period,
            partner=partner,
            reference=check.number,
            status='draft',
            currency=check.currency,
        )
        
        # Débito: Proveedor
        # Crédito: Valores en cartera
        JournalLine.objects.create(
            journal=journal,
            account=partner.default_account or (config.account_payable if config else None),
            debit_amount=check.amount,
            credit_amount=0,
            order=1
        )
        JournalLine.objects.create(
            journal=journal,
            account=config.account_values_in_portfolio if config else None,
            debit_amount=0,
            credit_amount=check.amount,
            order=2
        )
        
        journal.post()
        
        check.state = CheckState.RECONCILED
        check.dest_partner = partner
        check.dest_purchase_id = None
        check.save(update_fields=['state', 'dest_partner', 'dest_purchase'])
        
        CheckOperation.objects.create(
            check=check,
            operation_type='deliver',
            partner=partner,
            notes=f"Entregado a {partner.name} - Journal: {journal.number}"
        )
    
    @classmethod
    def cancel_check(cls, check: Check):
        """Cancela un cheque"""
        if check.state not in [CheckState.DRAFT, CheckState.HELD]:
            raise ValidationError("Solo se pueden cancelar cheques en borrador o en cartera.")
        
        check.state = CheckState.CANCELLED
        check.save(update_fields=['state'])
        
        CheckOperation.objects.create(
            check=check,
            operation_type='cancel',
            notes="Cheque anulado"
        )
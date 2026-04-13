from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class DocumentType(models.Model):
    """Tipos de documento para facturación Argentina (AFIP)"""
    DOCUMENT_CLASS = [
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de Crédito'),
        ('debit_note', 'Nota de Débito'),
    ]
    
    IVA_TYPE = [
        ('A', 'A - Responsable Inscripto'),
        ('B', 'B - Consumidor Final'),
        ('C', 'C - Monotributista/Exento'),
        ('M', 'M - Factura MiPyMEs'),
    ]
    
    code = models.CharField(max_length=10, unique=True, help_text='Código AFIP (ej: 001, 011)')
    name = models.CharField(max_length=100, help_text='Nombre del documento')
    document_class = models.CharField(max_length=20, choices=DOCUMENT_CLASS, default='invoice')
    iva_type = models.CharField(max_length=1, choices=IVA_TYPE, help_text='Tipo de IVA aplica')
    prefix = models.CharField(max_length=5, help_text='Prefijo para secuencia')
    next_number = models.PositiveIntegerField(default=1, help_text='Próximo número de secuencia')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_next_number(self):
        number = f"{self.prefix}-{self.next_number:08d}"
        self.next_number += 1
        self.save(update_fields=['next_number'])
        return number


class JournalStatus(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    POSTED = 'posted', 'Publicado'
    CANCELLED = 'cancelled', 'Anulado'


class JournalType(models.TextChoices):
    SALE = 'sale', 'Ventas'
    PURCHASE = 'purchase', 'Compras'
    CASH = 'cash', 'Caja'
    BANK = 'bank', 'Banco'
    GENERAL = 'general', 'General'


class Journal(models.Model):
    number = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=JournalStatus.choices, default=JournalStatus.DRAFT)
    period = models.ForeignKey("periods.AccountingPeriod", on_delete=models.PROTECT, related_name='journals')
    
    # Configuración de diario
    journal_type = models.CharField(max_length=20, choices=JournalType.choices, default=JournalType.GENERAL)
    journal_code = models.CharField(max_length=5, unique=True, help_text='Código corto del diario')
    currency = models.ForeignKey('locale.Currency', on_delete=models.SET_NULL, null=True, blank=True, related_name='journals', help_text='Moneda del diario')
    
    # Cuentas por defecto del diario
    default_account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_journals')
    
    reference = models.CharField(max_length=100, blank=True)
    partner = models.ForeignKey("partners.Partner", on_delete=models.SET_NULL, related_name='journals', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_journals', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-number']

    @property
    def company(self):
        """Obtiene la empresa del período"""
        return self.period.company if self.period else None

    def clean(self):
        if self.status == JournalStatus.POSTED and not self.posted_at:
            raise ValidationError("La fecha de publicación es obligatoria para los diarios publicados.")
        if self.status != JournalStatus.POSTED and self.posted_at:
            raise ValidationError("La fecha de publicación solo puede establecerse para diarios publicados.")
        if self.period.is_closed:
            raise ValidationError("No se pueden modificar diarios en un período cerrado.")
        if self.period.fiscal_year.is_locked:
            raise ValidationError(
                f"Año fiscal bloqueado hasta {self.period.fiscal_year.lock_date}. "
                "No se pueden realizar modificaciones."
            )
    
    def validate_balance(self):
        from django.db.models import Sum
        totals = self.lines.aggregate(debit=Sum('debit_amount'), credit=Sum('credit_amount'))
        if totals['debit'] != totals['credit']:
            raise ValidationError(f"El diario no está balanceado. Total Débito: {totals['debit']}, Total Crédito: {totals['credit']}")
    
    def post(self):
        from django.utils import timezone

        self.validate_balance()
        if not self.number:
            self.number = self._generate_number()
        
        self.status = JournalStatus.POSTED
        self.posted_at = timezone.now()
        self.save()
    
    def _generate_number(self):
        from django.db.models import Max

        year = self.date.year
        prefix = f"{year}-"

        last = Journal.objects.filter(
            number__startswith=prefix
        ).aggregate(Max('number'))

        last_num = last.get('number__max', None)
        if last_num and last_num.startswith(prefix):
            seq = int(last_num.split('-')[1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"

    def __str__(self):
        return f"{self.number} - {self.description}"


class JournalLine(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name='journalline_set')
    description = models.CharField(max_length=200, blank=True)
    debit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order = models.PositiveIntegerField(default=0)
    
    # Soporte multi-moneda
    currency = models.ForeignKey('locale.Currency', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_lines', help_text='Moneda de esta línea')
    currency_debit_amount = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, help_text='Monto en moneda de la línea (débito)')
    currency_credit_amount = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, help_text='Monto en moneda de la línea (crédito)')
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=8, default=1, help_text='Tipo de cambio (1 moneda extranjera = X moneda local)')

    class Meta:
        ordering = ['order']

    def clean(self):
        if not self.account.allows_movements:
            raise ValidationError(f"La cuenta {self.account} no permite movimientos.")
        if self.debit_amount < 0 or self.credit_amount < 0:
            raise ValidationError("Los montos de débito y crédito no pueden ser negativos.")
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError("Una línea no puede tener montos de débito y crédito al mismo tiempo.")
        
        # Validar compatibilidad de moneda con la cuenta
        if self.currency and self.account.currency:
            if self.currency != self.account.currency:
                raise ValidationError(
                    f"La cuenta {self.account.code} solo acepta movimientos en {self.account.currency.code}. "
                    f"La línea especifica {self.currency.code}."
                )
        
        # Validar montos en moneda de línea si es diferente a la empresa
        if self.journal and self.journal.period and self.journal.period.company:
            company = self.journal.period.company
            if company.currency_id and self.currency and self.currency != company.currency_id:
                has_amount_in_currency = (
                    (self.currency_debit_amount and self.currency_debit_amount > 0) or
                    (self.currency_credit_amount and self.currency_credit_amount > 0)
                )
                if not has_amount_in_currency:
                    raise ValidationError(
                        f"Para operaciones en {self.currency.code} debe especificar "
                        f"el monto en esa moneda (currency_debit_amount o currency_credit_amount)"
                    )
    
    def __str__(self):
        return f"{self.account.code} - {self.description} (Débito: {self.debit_amount}, Crédito: {self.credit_amount})"
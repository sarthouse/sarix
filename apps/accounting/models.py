from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class JournalStatus(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    POSTED = 'posted', 'Publicado'
    CANCELLED = 'cancelled', 'Anulado'

class Journal(models.Model):
    number = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=JournalStatus.choices, default=JournalStatus.DRAFT)
    period = models.ForeignKey("periods.AccountingPeriod", on_delete=models.PROTECT, related_name='journals')
    reference = models.CharField(max_length=100, blank=True)
    partner = models.ForeignKey("partners.Partner", on_delete=models.SET_NULL, related_name='journals', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_journals', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-number']

    def clean(self):
        if self.status == JournalStatus.POSTED and not self.posted_at:
            raise ValidationError("La fecha de publicación es obligatoria para los diarios publicados.")
        if self.status != JournalStatus.POSTED and self.posted_at:
            raise ValidationError("La fecha de publicación solo puede establecerse para diarios publicados.")
        if self.period.is_closed:
            raise ValidationError("No se pueden modificar diarios en un período cerrado.")
    
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

    class Meta:
        ordering = ['order']

    def clean(self):
        if not self.account.allows_movements:
            raise ValidationError(f"La cuenta {self.account} no permite movimientos.")
        if self.debit_amount < 0 or self.credit_amount < 0:
            raise ValidationError("Los montos de débito y crédito no pueden ser negativos.")
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError("Una línea no puede tener montos de débito y crédito al mismo tiempo.")

    
    def __str__(self):
        return f"{self.account.code} - {self.description} (Débito: {self.debit_amount}, Crédito: {self.credit_amount})"
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class AccountType(models.TextChoices):
    ASSET = 'activo', 'Activo'
    LIABILITY = 'pasivo', 'Pasivo'
    EQUITY = 'patrimonio', 'Patrimonio'
    REVENUE = 'ingreso', 'Ingreso'
    EXPENSE = 'egreso', 'Egreso'


class Account(MPTTModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    allows_movements = models.BooleanField(default=True)
    currency = models.ForeignKey(
        'locale.Currency', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='accounts',
        help_text='Moneda específica de la cuenta (opcional)'
    )
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='accounts',
        help_text='Empresa propietaria de la cuenta'
    )

    class MPTTMeta:
        order_insertion_by = ['code']

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
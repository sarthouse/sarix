from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import DateTimeField


class CostCenter(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='children'
    )
    
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cost_centers'
    )
    
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)
    
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Centro de Costo'
        verbose_name_plural = 'Centros de Costo'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CostCenterDistribution(models.Model):
    journal_line = models.ForeignKey(
        'accounting.JournalLine',
        on_delete=models.CASCADE,
        related_name='cost_distributions'
    )
    cost_center = models.ForeignKey('CostCenter', on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        verbose_name = 'Distribución Centro de Costo'
        verbose_name_plural = 'Distribuciones Centros de Costo'
        unique_together = [['journal_line', 'cost_center']]
    
    def clean(self):
        if self.percentage <= 0 or self.percentage > 100:
            raise ValidationError("El porcentaje debe estar entre 0 y 100")


class FixedExpenseFrequency(models.TextChoices):
    MONTHLY = 'monthly', 'Mensual'
    QUARTERLY = 'quarterly', 'Trimestral'
    ANNUAL = 'annual', 'Anual'


class FixedExpenseCategory(models.TextChoices):
    RENT = 'rent', 'Alquiler'
    SALARY = 'salary', 'Sueldos'
    SERVICES = 'services', 'Servicios'
    INSURANCE = 'insurance', 'Seguro'
    TAX = 'tax', 'Impuestos'
    DEPRECIATION = 'depreciation', 'Depreciación'
    OTHER = 'other', 'Otro'


class FixedExpense(models.Model):
    name = models.CharField(max_length=100)
    account = models.ForeignKey('accounts.Account', on_delete=models.PROTECT, related_name='fixed_expenses')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    frequency = models.CharField(max_length=20, choices=FixedExpenseFrequency.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    category = models.CharField(max_length=20, choices=FixedExpenseCategory.choices)
    is_active = models.BooleanField(default=True)
    
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = 'Gasto Fijo'
        verbose_name_plural = 'Gastos Fijos'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.amount}/{self.frequency}"


class CostAllocation(models.Model):
    expense = models.ForeignKey('FixedExpense', on_delete=models.CASCADE, related_name='allocations')
    cost_center = models.ForeignKey('CostCenter', on_delete=models.CASCADE, related_name='expense_allocations')
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        verbose_name = 'Allocación de Gasto'
        verbose_name_plural = 'Allocaciones de Gastos'
        unique_together = [['expense', 'cost_center']]
    
    def clean(self):
        if self.percentage <= 0 or self.percentage > 100:
            raise ValidationError("El porcentaje debe estar entre 0 y 100")


class CashFlowCategoryType(models.TextChoices):
    OPERATING = 'operating', 'Operaciones'
    FINANCING = 'financing', 'Financiamiento'
    INVESTING = 'investing', 'Inversión'


class CashFlowCategory(models.Model):
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CashFlowCategoryType.choices)
    account_ids = models.ManyToManyField('accounts.Account', related_name='cashflow_categories')
    
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Categoría Flujo de Caja'
        verbose_name_plural = 'Categorías Flujo de Caja'
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class CashFlowSourceType(models.TextChoices):
    INVOICE = 'invoice', 'Factura'
    PAYMENT = 'payment', 'Pago'
    FIXED_EXPENSE = 'fixed_expense', 'Gasto Fijo'
    MANUAL = 'manual', 'Manual'


class CashFlowLine(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    flow_type = models.CharField(max_length=10, choices=[
        ('inbound', 'Entrada'),
        ('outbound', 'Salida')
    ])
    description = models.CharField()
    partner = models.ForeignKey('partners.Partner', on_delete=models.SET_NULL, null=True, blank=True)
    source_type = models.CharField(max_length=20, choices=CashFlowSourceType.choices)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    is_actual = models.BooleanField(default=False)
    
    category = models.ForeignKey(
        'CashFlowCategory',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lines'
    )
    cost_center = models.ForeignKey(
        'CostCenter',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cashflow_lines'
    )
    
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Línea Flujo de Caja'
        verbose_name_plural = 'Líneas Flujo de Caja'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.flow_type} - {self.amount}"
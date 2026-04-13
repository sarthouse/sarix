from django.db import models


class IvaCondition(models.TextChoices):
    RESPONSABLE_INSCRITO = 'responsable_inscripto', 'Responsable Inscripto'
    MONOTRIBUTISTA = 'monotributista', 'Monotributista'
    EXENTO = 'exento', 'Exento'
    CONSUMIDOR_FINAL = 'consumidor_final', 'Consumidor Final'


class Company(models.Model):
    name = models.CharField(max_length=255)
    cuit = models.CharField(max_length=20, unique=True)
    currency = models.CharField(max_length=10, default='ARS', help_text='Código de moneda default (legacy)')
    currency_id = models.ForeignKey('locale.Currency', on_delete=models.SET_NULL, null=True, blank=True, related_name='companies', help_text='Moneda principal de la empresa')
    logo = models.ImageField(upload_to='company/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Dirección fiscal estructurada
    street = models.CharField(max_length=200, blank=True)
    street2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.ForeignKey('locale.State', null=True, blank=True, on_delete=models.SET_NULL, related_name='companies')
    country = models.ForeignKey('locale.Country', null=True, blank=True, on_delete=models.SET_NULL, related_name='companies')
    postal_code = models.CharField(max_length=20, blank=True)

    # Contacto
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    website = models.URLField(max_length=255, null=True, blank=True)

    # Datos fiscales Argentina
    iva_condition = models.CharField(
        max_length=30,
        choices=IvaCondition.choices,
        default=IvaCondition.RESPONSABLE_INSCRITO
    )
    activity_start_date = models.DateField(null=True, blank=True, help_text='Fecha de inicio de actividades ante AFIP')
    establishment_number = models.CharField(max_length=20, blank=True, help_text='Número de establecimiento')

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.name
    
    @classmethod
    def get(cls):
        return cls.objects.filter(is_active=True).first()


class CompanyConfig(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='config')
    
    # Cuentas default por empresa
    account_asset = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_asset',
        null=True, blank=True, help_text='Cuenta de inventario/mercaderías (activo)'
    )
    account_stock_valuation = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_stock_valuation',
        null=True, blank=True, help_text='Cuenta de valoración de inventario'
    )
    account_cogs = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_cogs',
        null=True, blank=True, help_text='Costo de ventas (egreso)'
    )
    account_revenue = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_revenue',
        null=True, blank=True, help_text='Ventas/Ingresos'
    )
    account_receivable = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_receivable',
        null=True, blank=True, help_text='Cuentas por cobrar'
    )
    account_payable = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_payable',
        null=True, blank=True, help_text='Cuentas por pagar'
    )
    
    # Cuentas adicionales para operaciones
    account_cash_diff_income = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_cash_diff_income',
        null=True, blank=True, help_text='Diferencias de caja - Ingreso'
    )
    account_cash_diff_expense = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_cash_diff_expense',
        null=True, blank=True, help_text='Diferencias de caja - Egreso'
    )
    account_exchange_gain = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_exchange_gain',
        null=True, blank=True, help_text='Ganancias por diferencia de cambio'
    )
    account_exchange_loss = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_exchange_loss',
        null=True, blank=True, help_text='Pérdidas por diferencia de cambio'
    )
    account_journal_suspense = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_suspense',
        null=True, blank=True, help_text='Cuenta de suspenso para diarios'
    )
    
    # Cuentas default para movimientos
    default_income_account = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_default_income',
        null=True, blank=True, help_text='Cuenta de ingresos por defecto'
    )
    default_expense_account = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_default_expense',
        null=True, blank=True, help_text='Cuenta de gastos por defecto'
    )
    
    account_cash = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_cash',
        null=True, blank=True, help_text='Cuenta de caja/efectivo'
    )
    account_bank = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_bank',
        null=True, blank=True, help_text='Cuenta de banco default'
    )
    
    account_values_in_portfolio = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_values_portfolio',
        null=True, blank=True, help_text='Valores en cartera (cheques propios)'
    )
    account_checks_rejected = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_checks_rejected',
        null=True, blank=True, help_text='Cheques rechazados'
    )
    account_third_party_checks = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_third_party_checks',
        null=True, blank=True, help_text='Cheques de terceros'
    )
    account_values_to_deposit = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_values_to_deposit',
        null=True, blank=True, help_text='Valores a depositar (en tránsito)'
    )
    
    default_perception_account = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_perceptions',
        null=True, blank=True, help_text='Cuenta default para percepciones'
    )
    default_withholding_account = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='companies_withholdings',
        null=True, blank=True, help_text='Cuenta default para retenciones'
    )
    perception_journal = models.ForeignKey(
        'accounting.Journal', on_delete=models.PROTECT, related_name='companies_perception_journals',
        null=True, blank=True, help_text='Diario para percepciones'
    )

    class Meta:
        verbose_name = 'Configuracion Contable'
        verbose_name_plural = 'Configuraciones Contables'

    def __str__(self):
        return f"Config - {self.company.name}"

    @classmethod
    def get(cls, company=None):
        company = company or Company.get()
        if not company:
            return None
        try:
            return cls.objects.get(company=company)
        except cls.DoesNotExist:
            return None
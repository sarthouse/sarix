from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True, help_text='ISO 3166-1 alpha-2')
    code_alpha3 = models.CharField(max_length=3, unique=True, blank=True, help_text='ISO 3166-1 alpha-3')
    numeric_code = models.CharField(max_length=3, unique=True, blank=True, help_text='ISO 3166-1 numeric')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['name']

    def __str__(self):
        return self.name


class State(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, help_text='Código provincial/estatal')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Provincia/Estado'
        verbose_name_plural = 'Provincias/Estados'
        ordering = ['country', 'name']
        unique_together = ['country', 'code']

    def __str__(self):
        return f"{self.name} ({self.country.code})"


class Currency(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True, help_text='ISO 4217')
    symbol = models.CharField(max_length=5, help_text='Símbolo monetario')
    decimal_places = models.PositiveIntegerField(default=2)
    position = models.CharField(
        max_length=10,
        choices=[('before', 'Antes del monto'), ('after', 'Después del monto')],
        default='after',
        help_text='Posición del símbolo'
    )
    is_active = models.BooleanField(default=True)
    is_company_currency = models.BooleanField(default=False, help_text='Moneda principal de la empresa')

    class Meta:
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        ordering = ['is_company_currency', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CurrencyRate(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates')
    rate = models.DecimalField(max_digits=20, decimal_places=8, help_text='Tasa de cambio respecto a la moneda de la empresa')
    date = models.DateField(help_text='Fecha de la tasa de cambio')
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, null=True, blank=True, related_name='currency_rates')

    class Meta:
        verbose_name = 'Tasa de Cambio'
        verbose_name_plural = 'Tasas de Cambio'
        ordering = ['-date']
        unique_together = ['currency', 'date', 'company']

    def __str__(self):
        return f"{self.currency.code} - {self.rate} ({self.date})"
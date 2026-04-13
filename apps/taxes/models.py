from django.db import models


class TaxType(models.TextChoices):
    PERCENT = 'percent', 'Porcentaje'
    FIXED = 'fixed', 'Fijo'
    DIVISION = 'division', 'División'


class TaxUse(models.TextChoices):
    SALE = 'sale', 'Venta'
    PURCHASE = 'purchase', 'Compra'
    NONE = 'none', 'Ninguno'


class TaxScope(models.TextChoices):
    SERVICE = 'service', 'Servicio'
    CONSUMABLE = 'consumable', 'Consumible'
    ALL = 'all', 'Todos'


class TaxGroup(models.TextChoices):
    IVA = 'iva', 'IVA'
    RETENCION = 'retencion', 'Retención'
    PERCEPCION = 'percepcion', 'Percepción'
    OTRO = 'otro', 'Otro'


class Tax(models.Model):
    name = models.CharField(max_length=100, help_text='Nombre del impuesto (ej: IVA 21%)')
    description = models.TextField(blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='Monto del impuesto')
    amount_type = models.CharField(max_length=20, choices=TaxType.choices, default=TaxType.PERCENT)
    
    type_tax_use = models.CharField(max_length=20, choices=TaxUse.choices, default=TaxUse.SALE)
    tax_scope = models.CharField(max_length=20, choices=TaxScope.choices, default=TaxScope.ALL)
    tax_group = models.CharField(max_length=20, choices=TaxGroup.choices, default=TaxGroup.IVA)
    
    include_base_amount = models.BooleanField(default=False, help_text='Incluye en base imponible')
    price_include = models.BooleanField(default=False, help_text='Precio incluye impuesto')
    is_base_affected = models.BooleanField(default=True, help_text='Base afectada por otros impuestos')
    
    account = models.ForeignKey(
        'accounts.Account', 
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='taxes',
        help_text='Cuenta contable para este impuesto'
    )
    
    children_taxes = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        blank=True,
        related_name='parent_taxes',
        help_text='Impuestos hijos (para grupos de impuestos)'
    )
    
    sequence = models.PositiveIntegerField(default=1, help_text='Orden de aplicación')
    is_active = models.BooleanField(default=True)
    
    TAX_TYPE_AR = [
        ('vat', 'IVA'),
        ('perception', 'Percepción'),
        ('retention', 'Retención'),
        ('other', 'Otro')
    ]
    
    tax_type = models.CharField(
        max_length=20,
        choices=TAX_TYPE_AR,
        default='vat',
        help_text='Tipo de impuesto (Argentina)'
    )
    
    PERCEPTION_BASE = [
        ('net', 'Neto gravado'),
        ('vat', 'Monto IVA'),
        ('total', 'Total factura')
    ]
    
    perception_base = models.CharField(
        max_length=20,
        choices=PERCEPTION_BASE,
        null=True, blank=True,
        help_text='Base de cálculo para percepciones'
    )
    
    APPLY_TO = [
        ('sale', 'Ventas'),
        ('purchase', 'Compras'),
        ('payment', 'Pagos')
    ]
    
    apply_to = models.CharField(
        max_length=20,
        choices=APPLY_TO,
        null=True, blank=True,
        help_text='Aplica a ventas, compras o pagos'
    )
    
    is_withholding = models.BooleanField(
        default=False,
        help_text='Es retención (monto negativo)'
    )
    
    withholding_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='withholding_taxes',
        help_text='Cuenta para retenciones/percepciones'
    )

    class Meta:
        verbose_name = 'Impuesto'
        verbose_name_plural = 'Impuestos'
        ordering = ['sequence', 'name']

    def __str__(self):
        return f"{self.name} ({self.amount}%)"
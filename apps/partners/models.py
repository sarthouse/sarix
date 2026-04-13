from django.db import models


class PartnerType(models.TextChoices):
    INDIVIDUAL = 'individual', 'Individual'
    EMPRESA = 'empresa', 'Empresa'


class IvaCondition(models.TextChoices):
    RESPONSABLE_INSCRITO = 'responsable_inscripto', 'Responsable Inscripto'
    MONOTRIBUTISTA = 'monotributista', 'Monotributista'
    EXENTO = 'exento', 'Exento'
    CONSUMIDOR_FINAL = 'consumidor_final', 'Consumidor Final'


class PartnerCategory(models.Model):
    name = models.CharField(max_length=100)
    color = models.PositiveIntegerField(default=1, help_text='Color para visualización')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    shortcut = models.CharField(max_length=20, blank=True, help_text='Abreviatura')

    class Meta:
        verbose_name = 'Categoría de Partner'
        verbose_name_plural = 'Categorías de Partners'
        ordering = ['name']

    def __str__(self):
        return self.name


class Partner(models.Model):
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)

    # Jerarquía empresa-contacto
    is_company = models.BooleanField(default=False, help_text='Indica si es una empresa (no un contacto individual)')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children', help_text='Empresa padre para contactos')

    # Categorías/Tags
    category = models.ManyToManyField(PartnerCategory, blank=True, related_name='partners')

    # Dirección estructurada
    street = models.CharField(max_length=200, blank=True)
    street2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.ForeignKey('locale.State', null=True, blank=True, on_delete=models.SET_NULL)
    country = models.ForeignKey('locale.Country', null=True, blank=True, on_delete=models.SET_NULL)
    postal_code = models.CharField(max_length=20, blank=True)

    # Datos fiscales Argentina
    cuit = models.CharField(max_length=13, blank=True, help_text='CUIT (ej: 20-12345678-9)')
    iva_condition = models.CharField(
        max_length=30,
        choices=IvaCondition.choices,
        default=IvaCondition.CONSUMIDOR_FINAL
    )
    default_document_type = models.ForeignKey(
        'accounting.DocumentType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='partners',
        help_text='Tipo de documento por defecto para facturación'
    )

    default_account = models.ForeignKey(
        "accounts.Account", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="partners"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
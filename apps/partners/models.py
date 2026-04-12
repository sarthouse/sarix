from django.db import models


class PartnerType(models.TextChoices):
    CLIENTE = "cliente", "Cliente"
    PROVEEDOR = "proveedor", "Proveedor"
    AMBOS = "ambos", "Ambos"

class Partner(models.Model):
    name = models.CharField(max_length=200)
    cuit = models.CharField(max_length=13, blank=True)
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
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

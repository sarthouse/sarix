from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    cuit = models.CharField(max_length=20, unique=True)
    fiscal_address = models.CharField(max_length=255)
    currency = models.CharField(max_length=10, default='ARS')
    logo = models.ImageField(upload_to='company/', null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.name
    
    @classmethod
    def get(cls):
        return cls.objects.first()
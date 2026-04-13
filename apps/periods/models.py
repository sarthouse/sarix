from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class FiscalYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    lock_date = models.DateField(null=True, blank=True, help_text='Fecha hasta la cual no se pueden modificar entradas')
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-start_date"]
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de cierre.")
        if self.lock_date:
            if self.lock_date < self.start_date:
                raise ValidationError("lock_date no puede ser anterior a start_date")
            if self.lock_date > self.end_date:
                raise ValidationError("lock_date no puede ser posterior a end_date")
    
    def __str__(self):
        return self.name
    
    @property
    def is_locked(self):
        if self.is_closed:
            return True
        if self.lock_date:
            return timezone.now().date() >= self.lock_date
        return False
    
class AccountingPeriod(models.Model):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="periods")
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = [["fiscal_year", "start_date"]]
        ordering = ["start_date"]

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de cierre.")
        if self.fiscal_year and (self.start_date < self.fiscal_year.start_date or self.end_date > self.fiscal_year.end_date):
            raise ValidationError("El período contable debe estar dentro del año fiscal.")
    
    def __str__(self):
        return f"{self.fiscal_year.name} - {self.name}"
    
    @property
    def is_locked(self):
        if self.is_closed:
            return True
        return self.fiscal_year.is_locked
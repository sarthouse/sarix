from django.db import models
from django.core.exceptions import ValidationError

class FiscalYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-start_date"]
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de cierre.")
    
    def __str__(self):
        return self.name
    
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
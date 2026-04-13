from django.db import models
from django.utils import timezone
from decimal import Decimal


class CurrencyService:
    """Servicio para manejo de monedas y tipos de cambio"""

    @classmethod
    def get_exchange_rate(cls, from_currency, to_currency, date=None, company=None):
        """
        Obtiene la tasa de cambio entre dos monedas para una fecha.
        Si no hay fecha, usa la última disponible.
        
        Args:
            from_currency: Moneda origen (Currency)
            to_currency: Moneda destino (Currency)
            date: Fecha de la tasa (opcional, usa hoy)
            company: Empresa para filtrar tasas específicas
            
        Returns:
            Decimal: Tasa de cambio (1 from_currency = X to_currency)
            
        Raises:
            ValidationError: Si no hay tasa disponible
        """
        from django.core.exceptions import ValidationError
        from apps.locale.models import CurrencyRate
        
        if from_currency == to_currency:
            return Decimal('1')
        
        date = date or timezone.now().date()
        
        rate = CurrencyRate.objects.filter(
            currency=from_currency,
            date__lte=date,
            company=company
        ).order_by('-date').first()
        
        if not rate:
            raise ValidationError(
                f"No hay tasa de cambio para {from_currency.code} en fecha {date}"
            )
        
        return rate.rate

    @classmethod
    def convert_amount(cls, amount, from_currency, to_currency, date=None, company=None):
        """
        Convierte un monto de una moneda a otra.
        
        Args:
            amount: Monto a convertir (Decimal)
            from_currency: Moneda origen (Currency)
            to_currency: Moneda destino (Currency)
            date: Fecha de la tasa (opcional)
            company: Empresa para filtrar tasas
            
        Returns:
            Decimal: Monto convertido en la moneda destino
        """
        if from_currency == to_currency:
            return amount
        
        rate = cls.get_exchange_rate(from_currency, to_currency, date, company)
        
        # Si la tasa es "1 moneda origen = X moneda destino"
        # Para convertir: monto * tasa
        return amount * rate

    @classmethod
    def get_or_create_rate(cls, currency, rate, date, company=None):
        """
        Obtiene o crea una tasa de cambio para una fecha.
        
        Args:
            currency: Moneda (Currency)
            rate: Tasa de cambio
            date: Fecha
            company: Empresa (opcional)
            
        Returns:
            CurrencyRate: La tasa creada o existente
        """
        from apps.locale.models import CurrencyRate
        
        rate_obj, created = CurrencyRate.objects.get_or_create(
            currency=currency,
            date=date,
            company=company,
            defaults={'rate': rate}
        )
        
        if not created and rate_obj.rate != rate:
            rate_obj.rate = rate
            rate_obj.save(update_fields=['rate'])
        
        return rate_obj


class AccountCurrencyValidator:
    """Validador de moneda en cuentas contables"""
    
    @classmethod
    def validate_line_currency(cls, journal_line):
        """
        Valida que la moneda de la línea sea compatible con la cuenta.
        
        Args:
            journal_line: JournalLine
            
        Raises:
            ValidationError: Si la moneda no es compatible
        """
        from django.core.exceptions import ValidationError
        
        account = journal_line.account
        line_currency = journal_line.currency
        
        # Si la cuenta tiene moneda específica, debe coincidir
        if account.currency and line_currency:
            if account.currency != line_currency:
                raise ValidationError(
                    f"La cuenta {account.code} ({account.currency.code}) "
                    f"solo acepta movimientos en {account.currency.code}. "
                    f"La línea especifica {line_currency.code}."
                )
        
        return True
    
    @classmethod
    def validate_required_amounts(cls, journal_line):
        """
        Valida que tenga montos en moneda de línea cuando es diferente a la empresa.
        
        Args:
            journal_line: JournalLine
            
        Raises:
            ValidationError: Si faltan montos requeridos
        """
        from django.core.exceptions import ValidationError
        
        journal = journal_line.journal
        company = journal.period.company if journal.period else None
        
        if not company or not company.currency_id:
            return True  # No hay empresa configurada, omitir validación
        
        line_currency = journal_line.currency
        company_currency = company.currency_id
        
        # Si la línea tiene moneda diferente a la empresa, requiere montos en moneda de línea
        if line_currency and line_currency != company_currency:
            has_amount_in_currency = (
                (journal_line.currency_debit_amount and journal_line.currency_debit_amount > 0) or
                (journal_line.currency_credit_amount and journal_line.currency_credit_amount > 0)
            )
            
            if not has_amount_in_currency:
                raise ValidationError(
                    f"Para operaciones en {line_currency.code} debe especificar "
                    f"el monto en esa moneda (currency_debit_amount o currency_credit_amount)"
                )
        
        return True


class ExchangeDifferenceCalculator:
    """Calculador de diferencias de cambio"""
    
    @classmethod
    def calculate_difference(cls, journal_line):
        """
        Calcula la diferencia de cambio entre monto en moneda de línea y monto en moneda empresa.
        
        Args:
            journal_line: JournalLine
            
        Returns:
            Decimal: Diferencia de cambio (positiva = ganancia, negativa = pérdida)
        """
        if not journal_line.currency:
            return Decimal('0')
        
        # Monto esperado en moneda empresa = monto en moneda línea * tipo de cambio
        if journal_line.debit_amount > 0:
            expected_amount = (journal_line.currency_debit_amount or Decimal('0')) * journal_line.exchange_rate
            return journal_line.debit_amount - expected_amount
        elif journal_line.credit_amount > 0:
            expected_amount = (journal_line.currency_credit_amount or Decimal('0')) * journal_line.exchange_rate
            return journal_line.credit_amount - expected_amount
        
        return Decimal('0')
    
    @classmethod
    def create_adjustment_entry(cls, journal, journal_line, description=None):
        """
        Crea un asiento de ajuste por diferencia de cambio.
        
        Args:
            journal: Journal origen
            journal_line: JournalLine que tiene la diferencia
            description: Descripción personalizada
            
        Returns:
            Journal: Nuevo diario con el ajuste
        """
        from django.db import transaction
        from apps.accounting.models import Journal, JournalLine
        from apps.company.models import CompanyConfig
        
        difference = cls.calculate_difference(journal_line)
        
        if difference == 0:
            return None
        
        company_config = CompanyConfig.get(journal.period.company if journal.period else None)
        
        if not company_config:
            return None
        
        # Determinar cuenta de ganancia o pérdida
        if difference > 0:
            account = company_config.account_exchange_gain
            debit_amount = difference
            credit_amount = Decimal('0')
        else:
            account = company_config.account_exchange_loss
            debit_amount = Decimal('0')
            credit_amount = abs(difference)
        
        if not account:
            return None
        
        description = description or f"Ajuste por diferencia de cambio - {journal_line.account.code}"
        
        with transaction.atomic():
            adjustment_journal = Journal.objects.create(
                date=journal.date,
                description=description,
                period=journal.period,
                reference=f"{journal.number}-AJ",
                partner=journal.partner
            )
            
            # Línea 1: cuenta original (contrarrestar)
            JournalLine.objects.create(
                journal=adjustment_journal,
                account=journal_line.account,
                description=f"Contrapartida - {journal_line.account.code}",
                debit_amount=journal_line.credit_amount,
                credit_amount=journal_line.debit_amount,
                order=0
            )
            
            # Línea 2: cuenta de diferencia de cambio
            JournalLine.objects.create(
                journal=adjustment_journal,
                account=account,
                description=description,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                order=1
            )
        
        return adjustment_journal
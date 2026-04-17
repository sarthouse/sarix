"""
Validadores de negocio centralizados.
Single source of truth para reglas de validación.
"""
from abc import ABC, abstractmethod
from django.core.exceptions import ValidationError


class BusinessValidator(ABC):
    """Base para todos validadores de negocio"""
    
    @staticmethod
    @abstractmethod
    def validate(obj):
        """
        Valida objeto. Raise ValidationError si hay problemas.
        
        Args:
            obj: Instancia del modelo a validar
            
        Raises:
            ValidationError: Con dict de errores por campo
        """
        pass


class SaleOrderValidator(BusinessValidator):
    """Validaciones para SaleOrder"""
    
    @staticmethod
    def validate(order):
        """Valida orden de venta"""
        errors = {}
        
        # Cliente requerido + válido
        if not order.customer:
            errors['customer'] = "Cliente requerido"
        elif not order.customer.is_customer:
            errors['customer'] = "Partner no es cliente"
        elif getattr(order.customer, 'blocked', False):
            errors['customer'] = "Cliente bloqueado"
        
        # Período validación
        if hasattr(order, 'period') and order.period:
            if getattr(order.period, 'is_closed', False):
                errors['period'] = "Período cerrado"
        
        # Para updates: requiere líneas
        if order.pk and hasattr(order, 'lines'):
            if not order.lines.exists():
                errors['lines'] = "Requiere al menos 1 línea"
        
        # Fecha validación
        if not order.date:
            errors['date'] = "Fecha requerida"
        
        # Warehouse requerido
        if not order.warehouse:
            errors['warehouse'] = "Almacén requerido"
        
        if errors:
            raise ValidationError(errors)


class SaleQuoteValidator(BusinessValidator):
    """Validaciones para SaleQuote"""
    
    @staticmethod
    def validate(quote):
        """Valida presupuesto de venta"""
        errors = {}
        
        if not quote.customer:
            errors['customer'] = "Cliente requerido"
        elif not quote.customer.is_customer:
            errors['customer'] = "Partner no es cliente"
        
        if not quote.warehouse:
            errors['warehouse'] = "Almacén requerido"
        
        if not quote.date:
            errors['date'] = "Fecha requerida"
        
        if quote.pk and hasattr(quote, 'lines'):
            if not quote.lines.exists():
                errors['lines'] = "Requiere líneas"
        
        if errors:
            raise ValidationError(errors)


class PurchaseOrderValidator(BusinessValidator):
    """Validaciones para PurchaseOrder"""
    
    @staticmethod
    def validate(order):
        """Valida orden de compra"""
        errors = {}
        
        if not order.partner:
            errors['partner'] = "Proveedor requerido"
        elif not getattr(order.partner, 'is_supplier', False):
            errors['partner'] = "Partner no es proveedor"
        
        if not order.warehouse:
            errors['warehouse'] = "Almacén requerido"
        
        if not order.date_order:
            errors['date_order'] = "Fecha requerida"
        
        if order.pk and hasattr(order, 'lines'):
            if not order.lines.exists():
                errors['lines'] = "Requiere líneas"
        
        if errors:
            raise ValidationError(errors)


class StockMovementValidator(BusinessValidator):
    """Validaciones para StockMovement"""
    
    @staticmethod
    def validate(movement):
        """Valida movimiento de stock"""
        errors = {}
        
        if not movement.product:
            errors['product'] = "Producto requerido"
        
        if not movement.warehouse_src:
            errors['warehouse_src'] = "Almacén origen requerido"
        
        if movement.qty <= 0:
            errors['qty'] = "Cantidad debe ser > 0"
        
        # Validar stock disponible en origen (si aplica)
        if movement.warehouse_src and movement.product and hasattr(movement, 'status'):
            if movement.status == 'draft':
                # Chequear disponibilidad en servicio, no acá
                pass
        
        if errors:
            raise ValidationError(errors)


class PaymentValidator(BusinessValidator):
    """Validaciones para Payment"""
    
    @staticmethod
    def validate(payment):
        """Valida pago"""
        errors = {}
        
        if not payment.partner:
            errors['partner'] = "Partner requerido"
        
        if payment.amount <= 0:
            errors['amount'] = "Monto debe ser > 0"
        
        if not payment.date:
            errors['date'] = "Fecha requerida"
        
        if not payment.payment_type:
            errors['payment_type'] = "Tipo pago requerido"
        
        if errors:
            raise ValidationError(errors)


class CheckValidator(BusinessValidator):
    """Validaciones para Check"""
    
    @staticmethod
    def validate(check):
        """Valida cheque"""
        errors = {}
        
        if not check.partner:
            errors['partner'] = "Partner requerido"
        
        if not check.number:
            errors['number'] = "Número requerido"
        
        if check.amount <= 0:
            errors['amount'] = "Monto debe ser > 0"
        
        if not check.date:
            errors['date'] = "Fecha requerida"
        
        if errors:
            raise ValidationError(errors)


class JournalValidator(BusinessValidator):
    """Validaciones para Journal (asiento contable)"""
    
    @staticmethod
    def validate(journal):
        """Valida asiento contable"""
        errors = {}
        
        if not journal.date:
            errors['date'] = "Fecha requerida"
        
        if hasattr(journal, 'period') and journal.period:
            if getattr(journal.period, 'is_closed', False):
                errors['period'] = "Período cerrado"
        
        if journal.pk and hasattr(journal, 'lines'):
            if not journal.lines.exists():
                errors['lines'] = "Requiere líneas"
            else:
                # Validar que sea balanceado
                debit_sum = sum(
                    float(line.debit_amount or 0) 
                    for line in journal.lines.all()
                )
                credit_sum = sum(
                    float(line.credit_amount or 0) 
                    for line in journal.lines.all()
                )
                if abs(debit_sum - credit_sum) > 0.01:
                    errors['balance'] = f"No balanceado: debe={debit_sum}, haber={credit_sum}"
        
        if errors:
            raise ValidationError(errors)

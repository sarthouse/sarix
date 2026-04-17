from django.db import models
from django.db import transaction
from django.db.models import F, Sum
from django.core.exceptions import ValidationError
from django.conf import settings as django_settings
from django.core.cache import cache

from apps.accounting.models import Journal, JournalLine
from apps.company.models import Company, CompanyConfig
from apps.accounts.models import Account

from .models import (
    StockMovement, Stock, StockAlert, StockQuant, Lot,
    ProductTemplate, Product, ProductType, Warehouse, StockCache
)


class StockCacheManager:
    """Manager inteligente para caché de stock (inspirado en Odoo)"""
    
    CACHE_TIMEOUT = 900  # 15 minutos
    CACHE_PREFIX = "sarix:stock"
    
    @classmethod
    def get_cache_key(cls, product_id, warehouse_id):
        """Genera key para Redis/cache"""
        return f"{cls.CACHE_PREFIX}:{product_id}:{warehouse_id}"
    
    @classmethod
    def get_or_fetch(cls, product_id, warehouse_id):
        """Obtiene cache de stock o lo computa si no existe"""
        cache_key = cls.get_cache_key(product_id, warehouse_id)
        
        # Intenta cache en memoria
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Si no existe, obtener del modelo StockCache
        try:
            cache_obj = StockCache.objects.get(
                product_id=product_id,
                warehouse_id=warehouse_id
            )
            result = {
                'qty_available': float(cache_obj.qty_available),
                'qty_reserved': float(cache_obj.qty_reserved),
                'qty_free': float(cache_obj.qty_free),
            }
        except StockCache.DoesNotExist:
            result = {
                'qty_available': 0.0,
                'qty_reserved': 0.0,
                'qty_free': 0.0,
            }
        
        # Guardar en cache en memoria
        cache.set(cache_key, result, cls.CACHE_TIMEOUT)
        return result
    
    @classmethod
    def invalidate(cls, product_id, warehouse_id):
        """Invalida caché para producto + almacén"""
        cache_key = cls.get_cache_key(product_id, warehouse_id)
        cache.delete(cache_key)
    
    @classmethod
    def invalidate_product(cls, product_id):
        """Invalida caché para todos almacenes del producto"""
        warehouses = Warehouse.objects.values_list('id', flat=True)
        for warehouse_id in warehouses:
            cls.invalidate(product_id, warehouse_id)
    
    @classmethod
    def update_cache(cls, product_id, warehouse_id, qty_available, qty_reserved):
        """Actualiza StockCache en BD + invalida caché en memoria"""
        cache_obj, created = StockCache.objects.get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={'qty_available': 0, 'qty_reserved': 0}
        )
        cache_obj.qty_available = qty_available
        cache_obj.qty_reserved = qty_reserved
        cache_obj.save()
        
        cls.invalidate(product_id, warehouse_id)


class CompanyConfigService:
    """Servicio para obtener/configurar cuentas contables por empresa."""
    
    @classmethod
    def get_config(cls, company=None):
        company = company or Company.get()
        if not company:
            return None
        try:
            return CompanyConfig.objects.get(company=company)
        except CompanyConfig.DoesNotExist:
            return None
    
    @classmethod
    def resolve_account(cls, account_type, request_data=None, company=None):
        account_field = f'account_{account_type}'
        if request_data and account_field in request_data:
            account_id = request_data.get(account_field)
            if account_id:
                try:
                    return Account.objects.get(id=account_id)
                except Account.DoesNotExist:
                    pass
        
        config = cls.get_config(company)
        if config:
            account = getattr(config, account_field, None)
            if account:
                return account
        
        setting_name = f'{account_type.upper()}_ACCOUNT_ID'
        account_id = getattr(django_settings, setting_name, None)
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        raise ValidationError(f"No hay cuenta configurada para {account_type}")
    
    @classmethod
    def get_inventory_accounts(cls, company=None):
        config = cls.get_config(company)
        return {
            'asset': config.account_asset if config else None,
            'cogs': config.account_cogs if config else None,
        }
    
    @classmethod
    def get_sales_accounts(cls, company=None):
        config = cls.get_config(company)
        return {
            'revenue': config.account_revenue if config else None,
            'receivable': config.account_receivable if config else None,
            'payable': config.account_payable if config else None,
        }


class StockQuantService:
    """Servicio para StockQuant - equivalente a stock.quant de Odoo"""
    
    @classmethod
    @transaction.atomic
    def apply_movement(cls, movement: StockMovement) -> StockQuant:
        """Ajusta stock usando StockQuant."""
        product = movement.product
        template = movement.template
        lot = movement.lot
        
        if template and template.product_type == ProductType.SERVICIO:
            return None
        
        if movement.movement_type in ('entrada', 'ajuste'):
            warehouse = movement.warehouse_dst
            quant, _ = StockQuant.objects.select_for_update().get_or_create(
                product=product,
                lot=lot,
                warehouse=warehouse,
                defaults={'quantity': 0, 'reserved': 0}
            )
            quant.quantity = F('quantity') + movement.qty
            quant.save(update_fields=['quantity'])
        
        elif movement.movement_type == 'salida':
            warehouse = movement.warehouse_src
            
            if lot:
                quant = StockQuant.objects.select_for_update().get(
                    product=product,
                    lot=lot,
                    warehouse=warehouse
                )
            else:
                quant = StockQuant.objects.select_for_update().filter(
                    product=product,
                    warehouse=warehouse,
                    lot__isnull=True
                ).first()
            
            if not quant or quant.available < movement.qty:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {quant.available if quant else 0}, "
                    f"Requerido: {movement.qty}"
                )
            quant.quantity = F('quantity') - movement.qty
            quant.save(update_fields=['quantity'])
        
        elif movement.movement_type == 'transferencia':
            quant_src = StockQuant.objects.select_for_update().filter(
                product=product,
                warehouse=movement.warehouse_src
            ).first()
            if not quant_src or quant_src.available < movement.qty:
                raise ValidationError("Stock insuficiente para transferencia.")
            
            quant_dst, _ = StockQuant.objects.select_for_update().get_or_create(
                product=product,
                lot=lot,
                warehouse=movement.warehouse_dst,
                defaults={'quantity': 0, 'reserved': 0}
            )
            quant_src.quantity = F('quantity') - movement.qty
            quant_src.save(update_fields=['quantity'])
            quant_dst.quantity = F('quantity') + movement.qty
            quant_dst.save(update_fields=['quantity'])
            quant = quant_dst
        
        return quant
    
    @classmethod
    def reserve(cls, product, warehouse, qty, lot=None) -> StockQuant:
        """Reserva stock."""
        query = {'product': product, 'warehouse': warehouse}
        if lot:
            query['lot'] = lot
        
        quant = StockQuant.objects.select_for_update().filter(**query).first()
        if not quant or quant.available < qty:
            raise ValidationError(f"Stock insuficiente para reservar.")
        
        quant.reserved = F('reserved') + qty
        quant.save(update_fields=['reserved'])
        return quant
    
    @classmethod
    def release_reservation(cls, product, warehouse, qty, lot=None) -> StockQuant:
        """Libera reserva."""
        query = {'product': product, 'warehouse': warehouse}
        if lot:
            query['lot'] = lot
        
        quant = StockQuant.objects.select_for_update().filter(**query).first()
        if quant:
            quant.reserved = F('reserved') - qty
            if quant.reserved < 0:
                quant.reserved = 0
            quant.save(update_fields=['reserved'])
        return quant
    
    @classmethod
    def get_available(cls, product, warehouse, lot=None):
        """Obtiene stock disponible."""
        query = {'product': product, 'warehouse': warehouse}
        if lot:
            query['lot'] = lot
        
        quant = StockQuant.objects.filter(**query).first()
        return quant.available if quant else 0
    
    @classmethod
    def get_total_by_template(cls, template, warehouse=None):
        """Stock total por template (todas las variaciones)."""
        query = models.Q(product__template=template)
        if warehouse:
            query &= models.Q(warehouse=warehouse)
        
        totals = StockQuant.objects.filter(query).aggregate(
            total_qty=Sum('quantity'),
            total_reserved=Sum('reserved')
        )
        return {
            'quantity': totals['total_qty'] or 0,
            'reserved': totals['total_reserved'] or 0,
            'available': (totals['total_qty'] or 0) - (totals['total_reserved'] or 0)
        }


class StockService:
    """Servicio legacy para Stock (compatibilidad)."""
    
    @staticmethod
    @transaction.atomic
    def apply_movement(movement: StockMovement) -> Stock:
        """Ajusta stock legacy."""
        template = movement.template
        product = movement.product
        
        if template and template.product_type == ProductType.SERVICIO:
            return None
        
        if movement.movement_type in ('entrada', 'ajuste'):
            warehouse = movement.warehouse_dst
            stock, _ = Stock.objects.select_for_update().get_or_create(
                template=template,
                product=product,
                warehouse=warehouse
            )
            stock.qty_available = F('qty_available') + movement.qty
            stock.save(update_fields=['qty_available'])
        
        elif movement.movement_type == 'salida':
            warehouse = movement.warehouse_src
            stock_query = {'template': template, 'warehouse': warehouse}
            if product:
                stock_query['product'] = product
            else:
                stock_query['product__isnull'] = True
            
            stock = Stock.objects.select_for_update().filter(**stock_query).first()
            if not stock or stock.qty_available < movement.qty:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {stock.qty_available if stock else 0}, "
                    f"Requerido: {movement.qty}"
                )
            stock.qty_available = F('qty_available') - movement.qty
            stock.save(update_fields=['qty_available'])
        
        elif movement.movement_type == 'transferencia':
            stock_src = Stock.objects.select_for_update().get(
                template=template,
                warehouse=movement.warehouse_src
            )
            if stock_src.qty_available < movement.qty:
                raise ValidationError("Stock insuficiente para transferencia.")
            stock_src.qty_available = F('qty_available') - movement.qty
            stock_src.save(update_fields=['qty_available'])
            
            stock_dst, _ = Stock.objects.select_for_update().get_or_create(
                template=template,
                product=product,
                warehouse=movement.warehouse_dst
            )
            stock_dst.qty_available = F('qty_available') + movement.qty
            stock_dst.save(update_fields=['qty_available'])
            stock = stock_dst
        
        return stock


class StockMovementService:
    """Servicio para movimientos de stock."""
    
    @classmethod
    @transaction.atomic
    def post(cls, movement: StockMovement, period_id: int, request_data: dict = None) -> StockMovement:
        """Publica un movimiento."""
        if movement.status != 'draft':
            raise ValidationError("Solo se pueden publicar movimientos en borrador.")
        
        product = movement.product
        template = movement.template
        
        if movement.movement_type in ('entrada', 'salida', 'ajuste'):
            if product and template.track_variation:
                StockQuantService.apply_movement(movement)
            else:
                StockService.apply_movement(movement)
        
        if movement.movement_type in ('entrada', 'salida', 'ajuste'):
            if template and template.product_type != ProductType.SERVICIO:
                account_data = request_data or {}
                cls._create_journal(movement, period_id, account_data)
        
        movement.status = 'posted'
        movement.posted_at = models.DateTimeField(auto_now_add=True)
        movement.save(update_fields=['status', 'posted_at'])
        
        return movement
    
    @classmethod
    @transaction.atomic
    def cancel(cls, movement: StockMovement) -> StockMovement:
        """Cancela un movimiento."""
        if movement.status != 'posted':
            raise ValidationError("Solo se pueden cancelar movimientos publicados.")
        
        template = movement.template
        
        if template and template.product_type != ProductType.SERVICIO:
            if movement.movement_type in ('entrada', 'ajuste'):
                StockService.apply_movement(movement)
            elif movement.movement_type == 'salida':
                StockService.apply_movement(movement)
        
        if movement.journal:
            movement.journal.status = 'cancelled'
            movement.journal.save()
        
        movement.status = 'cancelled'
        movement.save(update_fields=['status'])
        
        return movement
    
    @classmethod
    def _create_journal(cls, movement: StockMovement, period_id: int, request_data: dict):
        """Crea el journal contable."""
        from apps.periods.models import AccountingPeriod
        
        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValidationError("Periodo contable no encontrado.")
        
        movement_type = movement.movement_type
        amount = movement.qty * movement.unit_cost
        
        if movement_type == 'entrada':
            debit_account = CompanyConfigService.resolve_account('asset', request_data)
            credit_account = movement.partner.default_account if movement.partner else None
            if not credit_account:
                credit_account = CompanyConfigService.resolve_account('payable', request_data)
            description = f"Entrada {movement.get_product_sku()} - {movement.reference or ''}"
        
        elif movement_type == 'salida':
            debit_account = CompanyConfigService.resolve_account('cogs', request_data)
            credit_account = CompanyConfigService.resolve_account('asset', request_data)
            description = f"Salida {movement.get_product_sku()} - {movement.reference or ''}"
        
        elif movement_type == 'ajuste':
            debit_account = CompanyConfigService.resolve_account('asset', request_data)
            credit_account = CompanyConfigService.resolve_account('cogs', request_data)
            description = f"Ajuste {movement.get_product_sku()} - {movement.reference or ''}"
        
        else:
            return None
        
        journal = Journal.objects.create(
            date=movement.created_at.date(),
            description=description,
            period=period,
            partner=movement.partner,
            reference=movement.reference,
            status='draft',
        )
        
        JournalLine.objects.create(
            journal=journal,
            account=debit_account,
            debit_amount=amount,
            credit_amount=0,
            order=1,
        )
        JournalLine.objects.create(
            journal=journal,
            account=credit_account,
            debit_amount=0,
            credit_amount=amount,
            order=2,
        )
        
        journal.post()
        movement.journal = journal
        movement.save(update_fields=['journal'])
        
        return journal


class JournalService:
    pass


class StockAlertService:
    """Servicio para alertas de stock."""
    
    @staticmethod
    def check(quant: StockQuant):
        if quant.product.template.product_type == ProductType.SERVICIO:
            return
        
        if quant.quantity <= 0:
            StockAlert.objects.get_or_create(
                quant=quant,
                alert_type='sin_stock',
                resolved=False
            )
        elif quant.quantity <= quant.product.template.cost_price * 10:
            StockAlert.objects.get_or_create(
                quant=quant,
                alert_type='bajo_minimo',
                resolved=False
            )
    
    @classmethod
    def resolve(cls, alert: StockAlert):
        alert.resolved = True
        alert.save(update_fields=['resolved'])


class PriceService:
    """Servicio para calculo de precios."""
    
    @classmethod
    def get_price(cls, product: Product, customer=None, qty: int = 1):
        base_price = product.get_sale_price()
        discount = 0
        total = base_price * qty
        return {'unit_price': base_price, 'discount': discount, 'subtotal': total}
    
    @classmethod
    def calculate_line(cls, product, qty, discount_type=None, discount_value=0):
        unit_price = product.get_sale_price()
        
        if discount_type == 'percentage':
            discount = unit_price * qty * (discount_value / 100)
        elif discount_type == 'fixed':
            discount = discount_value
        else:
            discount = 0
        
        subtotal = (unit_price * qty) - discount
        return {'unit_price': unit_price, 'discount': discount, 'subtotal': subtotal}
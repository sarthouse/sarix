from django.db import models
from django.conf import settings
from django.utils import timezone


class ProductType(models.TextChoices):
    ALMACENABLE = 'almacenable', 'Almacenable'
    SERVICIO = 'servicio', 'Servicio'
    CONSUMIBLE = 'consumible', 'Consumible'


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
    
    # Cuentas contables por categoría (jerarquía Odoo)
    property_account_income = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='categories_income',
        null=True, blank=True, help_text='Cuenta de ingresos por defecto para esta categoría'
    )
    property_account_expense = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='categories_expense',
        null=True, blank=True, help_text='Cuenta de gastos por defecto para esta categoría'
    )
    property_account_stock_valuation = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='categories_stock_valuation',
        null=True, blank=True, help_text='Cuenta de valoración de inventario para esta categoría'
    )

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.name


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    symbol = models.CharField(max_length=5)
    category = models.CharField(
        max_length=20,
        choices=[
            ('unit', 'Unidad'),
            ('weight', 'Peso'),
            ('volume', 'Volumen'),
            ('box', 'Caja'),
        ],
        default='unit'
    )
    ratio = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @classmethod
    def get_default(cls):
        return cls.objects.get_or_create(
            code='un',
            defaults={'name': 'Unidad', 'code': 'un', 'symbol': 'un', 'category': 'unit'}
        )[0]

    def convert_to(self, target_uom, qty):
        return (self.ratio / target_uom.ratio) * qty

    def convert_from(self, source_uom, qty):
        return (source_uom.ratio / self.ratio) * qty


class Attribute(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Valor de Atributo'
        verbose_name_plural = 'Valores de Atributos'
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductTemplate(models.Model):
    """Producto base / Plantilla - equivalente a product.template de Odoo"""
    sku = models.CharField(max_length=50, unique=True)  # SKU base, ej: "CAM-001"
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.ALMACENABLE)
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='product_templates'
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    track_lot = models.BooleanField(default=False, help_text='Tracking por lote/serial')
    track_variation = models.BooleanField(default=False, help_text='Tracking por variante')
    is_active = models.BooleanField(default=True)
    
    # Cuentas contables específicas (override de categoría/empresa)
    property_account_income = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='product_templates_income',
        null=True, blank=True, help_text='Cuenta de ingresos específica para este producto'
    )
    property_account_expense = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='product_templates_expense',
        null=True, blank=True, help_text='Cuenta de gastos específica para este producto'
    )

    sale_tax_ids = models.ManyToManyField(
        'taxes.Tax',
        related_name='sale_product_templates',
        blank=True,
        help_text='Impuestos de venta aplicados automáticamente a este producto'
    )
    purchase_tax_ids = models.ManyToManyField(
        'taxes.Tax',
        related_name='purchase_product_templates',
        blank=True,
        help_text='Impuestos de compra aplicados automáticamente a este producto'
    )

    class Meta:
        verbose_name = 'Plantilla de Producto'
        verbose_name_plural = 'Plantillas de Producto'

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.unit_of_measure:
            self.unit_of_measure = UnitOfMeasure.get_default()
        super().save(*args, **kwargs)


class Product(models.Model):
    """Variante específica - equivalente a product.product de Odoo"""
    template = models.ForeignKey(ProductTemplate, on_delete=models.CASCADE, related_name='variations')
    sku = models.CharField(max_length=50, unique=True)  # SKU propio ej: "CAM-001-Roja-M"
    name = models.CharField(max_length=255)  # ej: "Roja - M"
    attribute_values = models.ManyToManyField(AttributeValue, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def get_cost_price(self):
        return self.cost_price or self.template.cost_price

    def get_sale_price(self):
        return self.sale_price or self.template.sale_price

    def get_sale_tax_ids(self):
        return self.template.sale_tax_ids

    def get_purchase_tax_ids(self):
        return self.template.purchase_tax_ids


# Forward declarations - se definen antes de usarlos
class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    partner = models.ForeignKey('partners.Partner', null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Deposito'
        verbose_name_plural = 'Depositos'

    def __str__(self):
        return f"{self.code} - {self.name}"

    def create_default_locations(self):
        """Crea locations por defecto para el warehouse"""
        locations_data = [
            {'name': 'Stock', 'code': 'STOCK', 'location_type': 'inventory'},
            {'name': 'Entrada', 'code': 'INPUT', 'location_type': 'supplier'},
            {'name': 'Salida', 'code': 'OUTPUT', 'location_type': 'customer'},
            {'name': 'Transito', 'code': 'TRANSIT', 'location_type': 'transit'},
        ]
        for loc_data in locations_data:
            Location.objects.get_or_create(
                warehouse=self,
                code=loc_data['code'],
                defaults={
                    'name': loc_data['name'],
                    'location_type': loc_data['location_type'],
                    'is_active': True
                }
            )


class LocationType(models.TextChoices):
    SUPPLIER = 'supplier', 'Proveedor virtual'
    INVENTORY = 'inventory', 'Inventario'
    PRODUCTION = 'production', 'Producción'
    CUSTOMER = 'customer', 'Cliente'
    TRANSIT = 'transit', 'Tránsito'
    INTERNAL = 'internal', 'Interno'


class Location(models.Model):
    """Ubicación dentro de un warehouse - equivalente a stock.location de Odoo"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='children')
    location_type = models.CharField(max_length=20, choices=LocationType.choices, default=LocationType.INTERNAL)
    is_active = models.BooleanField(default=True)
    is_scrap = models.BooleanField(default=False, help_text='Ubicación de desperdicio/scrap')

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        unique_together = ['warehouse', 'code']
        ordering = ['warehouse', 'code']

    def __str__(self):
        return f"{self.warehouse.code}/{self.code} - {self.name}"
    
    @property
    def full_name(self):
        return f"{self.warehouse.name} / {self.name}"
    
    @classmethod
    def get_default_src(cls, warehouse, picking_type_code):
        """Obtiene location origen por defecto según tipo de operación"""
        type_map = {
            'incoming': 'INPUT',
            'outgoing': 'STOCK',
            'internal': 'STOCK',
            'adjustment': 'STOCK',
        }
        code = type_map.get(picking_type_code, 'STOCK')
        return cls.objects.filter(warehouse=warehouse, code=code).first()
    
    @classmethod
    def get_default_dst(cls, warehouse, picking_type_code):
        """Obtiene location destino por defecto según tipo de operación"""
        type_map = {
            'incoming': 'STOCK',
            'outgoing': 'OUTPUT',
            'internal': 'STOCK',
            'adjustment': 'STOCK',
        }
        code = type_map.get(picking_type_code, 'STOCK')
        return cls.objects.filter(warehouse=warehouse, code=code).first()


class Lot(models.Model):
    """Lote/Serial - equivalente a stock.lot de Odoo"""
    number = models.CharField(max_length=50, unique=True)
    template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT, related_name='lots')
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, help_text='Ubicación actual del lote')
    date_in = models.DateField(auto_now_add=True)
    date_out = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['-date_in']

    def __str__(self):
        return f"{self.number} - {self.template.sku}"
    
    @property
    def warehouse(self):
        return self.location.warehouse if self.location else None


class StockQuant(models.Model):
    """Stock cuantizado - equivalente a stock.quant de Odoo"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quants')
    lot = models.ForeignKey(Lot, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='quants')
    quantity = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    reserved = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        verbose_name = 'Stock Cuantizado'
        verbose_name_plural = 'Stock Cuantizado'
        unique_together = ['product', 'lot', 'location']

    def __str__(self):
        lot_info = f" - {self.lot.number}" if self.lot else ""
        return f"{self.product.sku}{lot_info} - {self.location.code}: {self.quantity}"

    @property
    def available(self):
        return self.quantity - self.reserved
    
    @property
    def warehouse(self):
        return self.location.warehouse


class PickingTypeCode(models.TextChoices):
    INCOMING = 'incoming', 'Receipt/Entrada'
    OUTGOING = 'outgoing', 'Delivery/Salida'
    INTERNAL = 'internal', 'Internal Transfer'
    ADJUSTMENT = 'adjustment', 'Adjustment/Ajuste'


class PickingType(models.Model):
    """Tipo de operación - equivalente a stock.picking.type"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, choices=PickingTypeCode.choices)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='picking_types')
    color = models.PositiveIntegerField(default=0, help_text='Color para visualización')
    sequence_prefix = models.CharField(max_length=20, default='0000', help_text='Prefijo para numeración')
    
    # Locations por defecto
    default_location_src = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='picking_types_src'
    )
    default_location_dst = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='picking_types_dst'
    )
    
    # Configuración
    use_create_lots = models.BooleanField(default=False, help_text='Crear lotes al validar')
    use_existing_lots = models.BooleanField(default=True, help_text='Usar lotes existentes')
    allow_partial = models.BooleanField(default=True, help_text='Permitir entregas parciales')
    show_operations = models.BooleanField(default=False, help_text='Mostrar operaciones detalladas')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Operación'
        verbose_name_plural = 'Tipos de Operación'
        unique_together = ['warehouse', 'code']
        ordering = ['warehouse', 'code']

    def __str__(self):
        return f"{self.warehouse.code}/{self.code} - {self.name}"
    
    def get_next_number(self):
        from django.db.models import Max
        prefix = f"{self.warehouse.code}/{self.sequence_prefix}/"
        last = PickingType.objects.filter(
            warehouse=self.warehouse, code=self.code
        ).aggregate(Max('sequence_prefix'))
        # Por ahora retorna el prefijo + secuencia simple
        return f"{prefix}0001"


class Stock(models.Model):
    """Stock legacy - mantener por compatibilidad"""
    template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    qty_available = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    qty_reserved = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    qty_min = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        unique_together = [('template', 'warehouse'), ('product', 'warehouse')]
        verbose_name = 'Stock (legacy)'
        verbose_name_plural = 'Stocks (legacy)'

    def __str__(self):
        product_sku = self.product.sku if self.product else self.template.sku
        return f"{product_sku} - {self.warehouse.code}: {self.qty_available}"

    @property
    def qty_free(self):
        return self.qty_available - self.qty_reserved
    
    @classmethod
    def get_stock(cls, template, product=None, warehouse=None):
        """Obtiene stock por template o product"""
        if product:
            return cls.objects.filter(product=product, warehouse=warehouse).first()
        return cls.objects.filter(template=template, warehouse=warehouse).first()


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('transferencia', 'Transferencia'),
        ('ajuste', 'Ajuste'),
    ]
    STATUS = [
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('cancelled', 'Anulado'),
    ]
    
    # Picking type para mejor integración
    picking_type = models.ForeignKey(
        PickingType, null=True, blank=True, on_delete=models.PROTECT,
        help_text='Tipo de operación (receipt/delivery/internal)'
    )
    
    number = models.CharField(max_length=20, unique=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    
    template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    lot = models.ForeignKey(Lot, null=True, blank=True, on_delete=models.SET_NULL)
    lot_name = models.CharField(max_length=50, blank=True, help_text='Nombre de lote nuevo si no existe')
    
    # Locations (nuevo)
    location_src = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name='movements_out')
    location_dst = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name='movements_in')
    
    # Warehouse legacy (mantener para compatibilidad)
    warehouse_src = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name='movements_out')
    warehouse_dst = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name='movements_in')
    
    # Cantidad
    qty = models.DecimalField(max_digits=14, decimal_places=4)
    qty_done = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text='Cantidad validada')
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    
    # UOM
    uom = models.ForeignKey(UnitOfMeasure, null=True, blank=True, on_delete=models.PROTECT, help_text='Unidad de medida de la línea')
    
    # Origen y destino
    origin = models.CharField(max_length=100, blank=True, help_text='Documento origen (Sale, PO, etc)')
    partner = models.ForeignKey('partners.Partner', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Contabilidad
    journal = models.OneToOneField('accounting.Journal', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Tracking
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.number} - {self.get_movement_type_display()} - {self.get_product_sku()}"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # 1. Producto requerido
        if not self.product and not self.template:
            raise ValidationError("Debe especificar un producto")
        
        # 2. Cantidad positiva
        if not self.qty or self.qty <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        
        # 3. Location requerida según tipo
        if self.movement_type == 'salida':
            if not self.location_src and not self.warehouse_src:
                raise ValidationError("Una salida requiere una ubicación origen")
        
        if self.movement_type == 'entrada':
            if not self.location_dst and not self.warehouse_dst:
                raise ValidationError("Una entrada requiere una ubicación destino")
        
        if self.movement_type == 'transferencia':
            if not self.location_src and not self.warehouse_src:
                raise ValidationError("Una transferencia requiere ubicación origen")
            if not self.location_dst and not self.warehouse_dst:
                raise ValidationError("Una transferencia requiere ubicación destino")
            
            # Verificar que origen y destino sean diferentes
            src = self.location_src or self.warehouse_src
            dst = self.location_dst or self.warehouse_dst
            if src and dst and src == dst:
                raise ValidationError("La ubicación origen y destino no pueden ser iguales")
        
        # 4. Validar stock disponible para salidas (solo si no es ajuste)
        if self.movement_type in ['salida', 'transferencia'] and self.movement_type != 'ajuste':
            available = self._get_available_qty()
            if available < self.qty:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {available}, Solicitado: {self.qty}"
                )
        
        # 5. Solo draft puede modificarse
        if self.status not in ['draft', None]:
            raise ValidationError(f"No se puede modificar un movimiento en estado {self.get_status_display()}")
    
    def get_product_sku(self):
        return self.product.sku if self.product else (self.template.sku if self.template else 'N/A')
    
    def _get_available_qty(self):
        """Obtiene cantidad disponible en la ubicación origen"""
        product = self.product
        location = self.location_src
        warehouse = self.warehouse_src
        
        if location:
            quant = StockQuant.objects.filter(product=product, location=location).first()
            return quant.available if quant else 0
        
        if warehouse:
            quants = StockQuant.objects.filter(product=product, location__warehouse=warehouse)
            return sum(q.available for q in quants)
        
        return 0
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        
        # Si no tiene location pero tiene warehouse, usar locations por defecto
        if self.picking_type:
            if not self.location_src:
                self.location_src = Location.get_default_src(self.picking_type.warehouse, self.picking_type.code)
            if not self.location_dst:
                self.location_dst = Location.get_default_dst(self.picking_type.warehouse, self.picking_type.code)
        
        super().save(*args, **kwargs)

    def _generate_number(self):
        from django.db.models import Max
        
        # Usar picking_type si existe
        if self.picking_type:
            return self.picking_type.get_next_number()
        
        prefixes = {
            'entrada': 'ENT',
            'salida': 'SAL',
            'transferencia': 'TRF',
            'ajuste': 'AJU',
        }
        prefix = prefixes.get(self.movement_type, 'MOV')
        year = self.created_at.year if self.created_at else timezone.now().year
        prefix_str = f"{prefix}-{year}-"
        last = StockMovement.objects.filter(number__startswith=prefix_str).aggregate(Max('number'))
        last_num = last.get('number__max', None)
        if last_num and last_num.startswith(prefix_str):
            seq = int(last_num.split('-')[-1]) + 1
        else:
            seq = 1
        return f"{prefix_str}{seq:06d}"

    @property
    def total(self):
        return self.qty * self.unit_cost
    
    def post(self):
        """Ejecuta el movimiento de stock"""
        from django.db import transaction
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        
        if self.status != 'draft':
            raise ValidationError("Solo se pueden publicar movimientos en borrador")
        
        # Validar que tenga stock disponible para salidas
        if self.movement_type in ['salida', 'transferencia']:
            self.clean()  # Ejecuta validaciones
        
        with transaction.atomic():
            # Determinar locations origen y destino
            location_src = self.location_src
            location_dst = self.location_dst
            
            # Si solo hay warehouses (legacy), crear/quitar quants directamente
            if not location_src and self.warehouse_src:
                location_src = Location.get_default_src(self.warehouse_src, 'outgoing')
            if not location_dst and self.warehouse_dst:
                location_dst = Location.get_default_dst(self.warehouse_dst, 'incoming')
            
            product = self.product
            lot = self.lot
            
            # 1. Actualizar quant origen (salida/transferencia)
            if self.movement_type in ['salida', 'transferencia'] and location_src:
                quant_src = StockQuant.objects.filter(
                    product=product, lot=lot, location=location_src
                ).first()
                
                if quant_src:
                    # Desreservar si estaba reservado
                    if quant_src.reserved > 0:
                        reserved_to_release = min(quant_src.reserved, self.qty)
                        quant_src.reserved -= reserved_to_release
                    
                    # Disminuir cantidad
                    quant_src.quantity = max(Decimal('0'), quant_src.quantity - self.qty)
                    quant_src.save()
            
            # 2. Actualizar/crear quant destino (entrada/transferencia)
            if self.movement_type in ['entrada', 'transferencia'] and location_dst:
                quant_dst, created = StockQuant.objects.get_or_create(
                    product=product,
                    lot=lot,
                    location=location_dst,
                    defaults={'quantity': Decimal('0'), 'reserved': Decimal('0')}
                )
                quant_dst.quantity += self.qty
                quant_dst.save()
            
            # 3. Crear lote si se especificó nombre nuevo
            if self.lot_name and not self.lot:
                self.lot = Lot.objects.create(
                    number=self.lot_name,
                    template=self.product.template if self.product else self.template,
                    warehouse=location_dst.warehouse if location_dst else self.warehouse_dst
                )
                self.save(update_fields=['lot'])
            
            # 4. Actualizar estado
            self.status = 'posted'
            self.posted_at = timezone.now()
            self.qty_done = self.qty
            self.save()
            
            # 5. Crear movimiento de cadena si es transferencia (pendiente implementación)
            # if self.movement_type == 'transferencia':
            #     self._create_dest_movement()
    
    def action_assign(self):
        """Reserva stock disponible para el movimiento"""
        from django.core.exceptions import ValidationError
        
        if self.movement_type not in ['salida', 'transferencia']:
            return True
        
        available = self._get_available_qty()
        
        if available <= 0:
            return False  # No hay stock disponible
        
        location = self.location_src
        if not location and self.warehouse_src:
            location = Location.get_default_src(self.warehouse_src, 'outgoing')
        
        if not location:
            return False
        
        # Reservar en quant
        quant = StockQuant.objects.filter(
            product=self.product, location=location
        ).first()
        
        if not quant:
            return False
        
        from decimal import Decimal
        to_reserve = min(available, self.qty)
        
        quant.reserved += to_reserve
        quant.quantity -= to_reserve
        quant.save()
        
        return True
    
    def action_cancel(self):
        """Cancela el movimiento"""
        from django.core.exceptions import ValidationError
        
        if self.status == 'posted':
            # Deshacer el movimiento
            self._reverse_movement()
        
        self.status = 'cancelled'
        self.save()
    
    def _reverse_movement(self):
        """Revierte el movimiento de stock"""
        from decimal import Decimal
        
        location_src = self.location_src
        location_dst = self.location_dst
        
        if not location_src and self.warehouse_src:
            location_src = Location.get_default_src(self.warehouse_src, 'outgoing')
        if not location_dst and self.warehouse_dst:
            location_dst = Location.get_default_dst(self.warehouse_dst, 'incoming')
        
        product = self.product
        lot = self.lot
        qty = self.qty_done or self.qty
        
        # Revertir: entrada = quitar, salida = devolver
        if self.movement_type == 'entrada' and location_src:
            quant = StockQuant.objects.filter(
                product=product, lot=lot, location=location_src
            ).first()
            if quant:
                quant.quantity = max(Decimal('0'), quant.quantity - qty)
                quant.save()
        
        if self.movement_type in ['salida', 'transferencia'] and location_dst:
            quant_dst, created = StockQuant.objects.get_or_create(
                product=product, lot=lot, location=location_dst,
                defaults={'quantity': Decimal('0'), 'reserved': Decimal('0')}
            )
            quant_dst.quantity += qty
            quant_dst.save()


class StockAlert(models.Model):
    ALERT_TYPES = [
        ('bajo_minimo', 'Bajo minimo'),
        ('sin_stock', 'Sin stock')
    ]
    quant = models.ForeignKey(StockQuant, on_delete=models.CASCADE, null=True, blank=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerta de Stock'
        verbose_name_plural = 'Alertas de Stock'

    def __str__(self):
        if self.quant:
            return f"{self.get_alert_type_display()} - {self.quant.product.sku}"
        return f"{self.get_alert_type_display()} - {self.stock.template.sku}"
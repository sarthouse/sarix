import requests
import base64
import json
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    WooStore, WooProductMap, WooCategoryMap, 
    WooCustomerMap, WooOrderMap, WooCouponMap, WooTaxMapping
)
from apps.inventory.models import ProductTemplate, Product, Category, Stock, Warehouse
from apps.partners.models import Partner
from apps.sales.models import SaleOrder, SaleOrderLine
from apps.taxes.models import Tax


class WooCommerceAPIError(Exception):
    pass


class WooClient:
    """Cliente para la API de WooCommerce"""
    
    def __init__(self, store: WooStore):
        self.store = store
        self.url = store.url.rstrip('/')
        self.version = 'wc/v3'
        self.auth = (store.consumer_key, store.consumer_secret)
    
    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.url}/wp-json/{self.version}/{endpoint}"
        try:
            response = requests.request(
                method, url, 
                json=data, params=params,
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                raise WooCommerceAPIError(f"{error_data.get('code', 'error')}: {error_data.get('message', str(e))}")
            except:
                raise WooCommerceAPIError(f"HTTP {response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise WooCommerceAPIError(f"Connection error: {str(e)}")
    
    # Products
    def get_products(self, params: dict = None) -> List[dict]:
        return self._request('GET', 'products', params=params)
    
    def get_product(self, product_id: int) -> dict:
        return self._request('GET', f'products/{product_id}')
    
    def update_product(self, product_id: int, data: dict) -> dict:
        return self._request('PUT', f'products/{product_id}', data=data)
    
    def get_product_variations(self, parent_id: int, params: dict = None) -> List[dict]:
        return self._request('GET', f'products/{parent_id}/variations', params=params)
    
    def create_product(self, data: dict) -> dict:
        return self._request('POST', 'products', data=data)
    
    # Categories
    def get_categories(self, params: dict = None) -> List[dict]:
        return self._request('GET', 'products/categories', params=params)
    
    # Orders
    def get_orders(self, params: dict = None) -> List[dict]:
        return self._request('GET', 'orders', params=params)
    
    def get_order(self, order_id: int) -> dict:
        return self._request('GET', f'orders/{order_id}')
    
    # Customers
    def get_customers(self, params: dict = None) -> List[dict]:
        return self._request('GET', 'customers', params=params)
    
    def get_customer(self, customer_id: int) -> dict:
        return self._request('GET', f'customers/{customer_id}')
    
    # Coupons
    def get_coupons(self, params: dict = None) -> List[dict]:
        return self._request('GET', 'coupons', params=params)
    
    # Tax Classes
    def get_tax_classes(self) -> List[dict]:
        return self._request('GET', 'taxes/classes')
    
    # Webhooks
    def get_webhooks(self, params: dict = None) -> List[dict]:
        return self._request('GET', 'webhooks', params=params)
    
    def create_webhook(self, data: dict) -> dict:
        return self._request('POST', 'webhooks', data=data)
    
    def update_webhook(self, webhook_id: int, data: dict) -> dict:
        return self._request('PUT', f'webhooks/{webhook_id}', data=data)
    
    def delete_webhook(self, webhook_id: int) -> dict:
        return self._request('DELETE', f'webhooks/{webhook_id}')


class WooSyncService:
    """Servicio de sincronización con WooCommerce"""
    
    @classmethod
    def get_client(cls, store: WooStore) -> WooClient:
        return WooClient(store)
    
    # === SYNC PRODUCTS ===
    @classmethod
    @transaction.atomic
    def sync_products(cls, store: WooStore, full: bool = False) -> dict:
        """Sincroniza productos desde WooCommerce"""
        client = cls.get_client(store)
        
        if not store.sync_products:
            return {'skipped': True, 'reason': 'sync_products disabled'}
        
        params = {'per_page': 100}
        if not full:
            params['updated_at'] = store.last_sync_products.isoformat() if store.last_sync_products else None
        
        woo_products = client.get_products(params)
        
        created = 0
        updated = 0
        
        for woo_product in woo_products:
            try:
                cls._sync_single_product(store, woo_product, client)
                created += 1
            except Exception as e:
                updated += 1
        
        store.last_sync_products = timezone.now()
        store.save(update_fields=['last_sync_products'])
        
        return {'created': created, 'updated': updated, 'total': len(woo_products)}
    
    @classmethod
    def _sync_single_product(cls, store: WooStore, woo_product: dict, client: WooClient):
        """Sincroniza un producto individual"""
        
        # Check if simple or variable
        product_type = woo_product.get('type', 'simple')
        
        # Handle categories
        category = None
        if woo_product.get('categories'):
            cat_id = woo_product['categories'][0].get('id')
            category = cls._get_or_create_category(store, cat_id, client)
        
        # Create ProductTemplate
        track_variation = product_type == 'variable'
        
        template, _ = ProductTemplate.objects.update_or_create(
            sku=f"WOO-{woo_product['id']}",
            defaults={
                'name': woo_product.get('name', 'Sin nombre'),
                'category': category,
                'product_type': 'variable' if product_type == 'variable' else 'almenable',
                'cost_price': Decimal(woo_product.get('regular_price') or 0),
                'sale_price': Decimal(woo_product.get('price') or woo_product.get('regular_price') or 0),
                'is_active': woo_product.get('status') == 'publish',
                'track_variation': track_variation,
            }
        )
        
        # Sync tags
        woo_tags = woo_product.get('tags', [])
        if woo_tags:
            from apps.inventory.models import ProductTag
            tags = []
            for woo_tag in woo_tags:
                tag, _ = ProductTag.objects.get_or_create(
                    woo_tag_id=woo_tag.get('id'),
                    defaults={
                        'name': woo_tag.get('name', ''),
                        'slug': woo_tag.get('slug', '')
                    }
                )
                tags.append(tag)
            template.tags.set(tags)
        
        # Sync attributes for variable products
        if product_type == 'variable':
            woo_attributes = woo_product.get('attributes', [])
            cls._sync_product_attributes(store, template, woo_attributes)
        
        # Create mapping
        map_obj, _ = WooProductMap.objects.update_or_create(
            woo_store=store,
            woo_product_id=woo_product['id'],
            defaults={
                'product_template': template,
                'woo_sku': woo_product.get('sku'),
            }
        )
        
        # For variable products, sync variations
        if product_type == 'variable':
            variations = client.get_product_variations(woo_product['id'])
            for variation in variations:
                cls._sync_variation(store, template, variation)
        
        # Simple product - create Product
        if product_type == 'simple':
            product, _ = Product.objects.update_or_create(
                template=template,
                defaults={'sku': woo_product.get('sku') or f"WOO-{woo_product['id']}"}
            )
            map_obj.product = product
            map_obj.save()
        
        return template
    
    @classmethod
    def _sync_product_attributes(cls, store: WooStore, template: ProductTemplate, woo_attributes: list):
        """Sincroniza atributos de producto desde WooCommerce"""
        from apps.inventory.models import Attribute, AttributeValue
        
        for woo_attr in woo_attributes:
            attr_name = woo_attr.get('name', '')
            attr_options = woo_attr.get('options', [])
            
            if not attr_name:
                continue
            
            # Determinar si es global (taxonomy) o custom
            is_global = woo_attr.get('is_taxonomy', False)
            
            if is_global:
                # Global attribute - buscar por nombre (sin pa_ prefix)
                attr, _ = Attribute.objects.get_or_create(
                    name=attr_name,
                    defaults={'woo_attribute_id': woo_attr.get('id')}
                )
            else:
                # Custom attribute - crear si no existe
                attr, _ = Attribute.objects.get_or_create(name=attr_name)
            
            # Crear valores de atributos
            for option in attr_options:
                attr_value, _ = AttributeValue.objects.get_or_create(
                    attribute=attr,
                    value=option
                )
    
    @classmethod
    def _sync_variation(cls, store: WooStore, template: ProductTemplate, variation: dict):
        """Sincroniza una variación"""
        var_sku = variation.get('sku') or f"{template.sku}-VAR-{variation['id']}"
        
        product, _ = Product.objects.update_or_create(
            template=template,
            sku=var_sku,
            defaults={
                'name': variation.get('name', template.name),
                'cost_price': Decimal(variation.get('regular_price') or 0),
            }
        )
        
        WooProductMap.objects.update_or_create(
            woo_store=store,
            woo_product_id=variation['product_id'],
            variation_id=variation['id'],
            defaults={
                'product_template': template,
                'product': product,
                'woo_sku': var_sku,
            }
        )
        
        return product
    
    @classmethod
    def _get_or_create_category(cls, store: WooStore, category_id: int, client: WooClient) -> Optional[Category]:
        """Obtiene o crea una categoría"""
        if not category_id:
            return None
        
        mapping = WooCategoryMap.objects.filter(
            woo_store=store, woo_category_id=category_id
        ).first()
        if mapping:
            return mapping.category
        
        # Fetch from WooCommerce
        try:
            woo_cat = client._request('GET', f'products/categories/{category_id}')
            category, _ = Category.objects.get_or_create(
                name=woo_cat.get('name', 'Sin categoría'),
                defaults={
                    'name': woo_cat.get('name', 'Sin categoría'),
                }
            )
            
            WooCategoryMap.objects.create(
                woo_store=store,
                woo_category_id=category_id,
                category=category
            )
            return category
        except:
            return None
    
    # === SYNC CATEGORIES ===
    @classmethod
    @transaction.atomic
    def sync_categories(cls, store: WooStore) -> dict:
        """Sincroniza categorías"""
        client = cls.get_client(store)
        
        if not store.sync_categories:
            return {'skipped': True}
        
        woo_categories = client.get_categories({'per_page': 100})
        
        created = 0
        for woo_cat in woo_categories:
            try:
                category, _ = Category.objects.get_or_create(
                    name=woo_cat.get('name', 'Sin categoría')
                )
                
                WooCategoryMap.objects.update_or_create(
                    woo_store=store,
                    woo_category_id=woo_cat['id'],
                    defaults={'category': category}
                )
                created += 1
            except:
                pass
        
        store.last_sync_categories = timezone.now()
        store.save(update_fields=['last_sync_categories'])
        
        return {'created': created}
    
    # === SYNC CUSTOMERS ===
    @classmethod
    @transaction.atomic
    def sync_customers(cls, store: WooStore) -> dict:
        """Sincroniza clientes"""
        client = cls.get_client(store)
        
        if not store.sync_customers:
            return {'skipped': True}
        
        woo_customers = client.get_customers({'per_page': 100})
        
        created = 0
        for woo_cust in woo_customers:
            try:
                # Get CUIT from billing.billing_dni or meta_data._billing_dni
                billing = woo_cust.get('billing', {})
                cuit = billing.get('dni')
                
                if not cuit:
                    meta_data = woo_cust.get('meta_data', [])
                    for meta in meta_data:
                        if meta.get('key') == '_billing_dni':
                            cuit = meta.get('value')
                            break
                
                partner, _ = Partner.objects.get_or_create(
                    email=woo_cust.get('email'),
                    defaults={
                        'name': f"{woo_cust.get('first_name', '')} {woo_cust.get('last_name', '')}".strip() or woo_cust.get('email', 'Cliente Woo'),
                        'is_customer': True,
                    }
                )
                
                # Update CUIT if found and partner doesn't have one
                if cuit and not partner.cuit:
                    partner.cuit = str(cuit)
                    partner.save(update_fields=['cuit'])
                
                WooCustomerMap.objects.update_or_create(
                    woo_store=store,
                    woo_customer_id=woo_cust['id'],
                    defaults={'partner': partner}
                )
                created += 1
            except:
                pass
        
        store.last_sync_customers = timezone.now()
        store.save(update_fields=['last_sync_customers'])
        
        return {'created': created}
    
    @classmethod
    def _sync_single_customer(cls, store: WooStore, woo_customer: dict):
        """Sincroniza un cliente individual"""
        
        # Get CUIT from billing.billing_dni or meta_data._billing_dni
        billing = woo_customer.get('billing', {})
        cuit = billing.get('dni')
        
        if not cuit:
            meta_data = woo_customer.get('meta_data', [])
            for meta in meta_data:
                if meta.get('key') == '_billing_dni':
                    cuit = meta.get('value')
                    break
        
        partner, _ = Partner.objects.get_or_create(
            email=woo_customer.get('email'),
            defaults={
                'name': f"{woo_customer.get('first_name', '')} {woo_customer.get('last_name', '')}".strip() or woo_customer.get('email', 'Cliente Woo'),
                'is_customer': True,
            }
        )
        
        # Update CUIT if found and partner doesn't have one
        if cuit and not partner.cuit:
            partner.cuit = str(cuit)
            partner.save(update_fields=['cuit'])
        
        WooCustomerMap.objects.update_or_create(
            woo_store=store,
            woo_customer_id=woo_customer['id'],
            defaults={'partner': partner}
        )
        
        return partner
    
    # === SYNC ORDERS ===
    @classmethod
    @transaction.atomic
    def sync_orders(cls, store: WooStore, status_filter: List[str] = None) -> dict:
        """Sincroniza órdenes desde WooCommerce"""
        client = cls.get_client(store)
        
        if not store.sync_orders:
            return {'skipped': True}
        
        params = {'per_page': 50}
        if status_filter:
            params['status'] = ','.join(status_filter)
        
        woo_orders = client.get_orders(params)
        
        created = 0
        errors = 0
        
        for woo_order in woo_orders:
            try:
                # Check if already mapped
                existing = WooOrderMap.objects.filter(
                    woo_store=store, woo_order_id=woo_order['id']
                ).first()
                if existing:
                    continue
                
                sale_order = cls._create_sale_order_from_woo(store, woo_order)
                created += 1
            except Exception as e:
                errors += 1
        
        store.last_sync_orders = timezone.now()
        store.save(update_fields=['last_sync_orders'])
        
        return {'created': created, 'errors': errors}
    
    @classmethod
    def _create_sale_order_from_woo(cls, store: WooStore, woo_order: dict) -> SaleOrder:
        """Crea una SaleOrder desde datos de WooCommerce"""
        
        # Get or create customer
        customer = None
        customer_id = woo_order.get('customer_id')
        if customer_id:
            cust_map = WooCustomerMap.objects.filter(
                woo_store=store, woo_customer_id=customer_id
            ).first()
            if cust_map:
                customer = cust_map.partner
        
        if not customer:
            # Create from billing info
            billing = woo_order.get('billing', {})
            
            # Get CUIT from billing.billing_dni or meta_data._billing_dni
            cuit = billing.get('dni')
            if not cuit:
                meta_data = woo_order.get('meta_data', [])
                for meta in meta_data:
                    if meta.get('key') == '_billing_dni':
                        cuit = meta.get('value')
                        break
            
            customer, _ = Partner.objects.get_or_create(
                email=billing.get('email'),
                defaults={
                    'name': f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or billing.get('email', 'Cliente'),
                    'is_customer': True,
                    'street': billing.get('address_1'),
                    'city': billing.get('city'),
                    'state': billing.get('state'),
                    'cuit': str(cuit) if cuit else None,
                }
            )
        
        # Create SaleOrder
        from apps.sales.models import SaleOrderStatus
        status_map = store.get_status_map()
        woo_status = woo_order.get('status', 'pending')
        sarix_status = status_map.get(woo_status, 'draft')
        
        # Get default warehouse
        warehouse = Warehouse.objects.filter(is_active=True).first()
        
        # Extract metadata (excluding _billing_dni already used for customer)
        woo_meta = woo_order.get('meta_data', [])
        
        sale_order = SaleOrder.objects.create(
            customer=customer,
            warehouse=warehouse,
            status=sarix_status,
            date=woo_order.get('date_created', '').split('T')[0],
            notes=f"WooCommerce Order #{woo_order.get('number')}",
            woo_metadata=woo_meta,
            woo_order_id=woo_order.get('id')
        )
        
        # Add lines
        line_items = woo_order.get('line_items', [])
        for idx, item in enumerate(line_items):
            product = None
            
            # Find product by SKU or mapping
            product_map = WooProductMap.objects.filter(
                woo_store=store, woo_product_id=item.get('product_id')
            ).first()
            if product_map and product_map.product:
                product = product_map.product
            
            if not product:
                # Create placeholder product
                template, _ = ProductTemplate.objects.get_or_create(
                    sku=f"WOO-UNK-{item.get('product_id')}",
                    defaults={
                        'name': item.get('name', 'Producto importado'),
                        'product_type': 'almenable',
                    }
                )
                product, _ = Product.objects.get_or_create(
                    template=template,
                    sku=f"WOO-UNK-{item.get('product_id')}"
                )
            
            # Get line metadata (attributes, etc)
            line_meta = item.get('meta_data', [])
            
            SaleOrderLine.objects.create(
                order=sale_order,
                product=product,
                qty=item.get('quantity', 1),
                unit_price=Decimal(str(item.get('price', 0))),
                woo_line_metadata=line_meta if line_meta else None
            )
        
        # Create SaleOrder
        from apps.sales.models import SaleOrderStatus
        status_map = store.get_status_map()
        woo_status = woo_order.get('status', 'pending')
        sarix_status = status_map.get(woo_status, 'draft')
        
        # Get default warehouse
        warehouse = Warehouse.objects.filter(is_active=True).first()
        
        sale_order = SaleOrder.objects.create(
            customer=customer,
            warehouse=warehouse,
            status=sarix_status,
            date=woo_order.get('date_created', '').split('T')[0],
            notes=f"WooCommerce Order #{woo_order.get('number')}"
        )
        
        # Add lines
        line_items = woo_order.get('line_items', [])
        for idx, item in enumerate(line_items):
            product = None
            
            # Find product by SKU or mapping
            product_map = WooProductMap.objects.filter(
                woo_store=store, woo_product_id=item.get('product_id')
            ).first()
            if product_map and product_map.product:
                product = product_map.product
            
            if not product:
                # Create placeholder product
                template, _ = ProductTemplate.objects.get_or_create(
                    sku=f"WOO-UNK-{item.get('product_id')}",
                    defaults={
                        'name': item.get('name', 'Producto importado'),
                        'product_type': 'almenable',
                    }
                )
                product, _ = Product.objects.get_or_create(
                    template=template,
                    sku=f"WOO-UNK-{item.get('product_id')}"
                )
            
            SaleOrderLine.objects.create(
                order=sale_order,
                product=product,
                qty=item.get('quantity', 1),
                unit_price=Decimal(str(item.get('price', 0))),
            )
        
        # Apply coupon discount if exists
        coupon_lines = woo_order.get('coupon_lines', [])
        for coupon in coupon_lines:
            coupon_code = coupon.get('code', '')
            if coupon_code:
                mapping = WooCouponMap.objects.filter(
                    woo_store=store, coupon_code=coupon_code.upper()
                ).first()
                if mapping:
                    discount_amount = Decimal(str(coupon.get('discount', '0').replace('-', '').replace('.', '').replace(',', '.')))
                    sale_order.subtotal -= discount_amount
        
        # Save mapping
        WooOrderMap.objects.create(
            woo_store=store,
            woo_order_id=woo_order['id'],
            sale_order=sale_order
        )
        
        # Auto-deliver if completed
        from apps.sales.services import SaleOrderService
        if sarix_status == 'delivered':
            try:
                SaleOrderService.deliver(sale_order, None)
            except:
                pass
        
        return sale_order
    
    # === SYNC COUPONS ===
    @classmethod
    @transaction.atomic
    def sync_coupons(cls, store: WooStore) -> dict:
        """Sincroniza cupones/descuentos"""
        client = cls.get_client(store)
        
        if not store.sync_coupons:
            return {'skipped': True}
        
        woo_coupons = client.get_coupons({'per_page': 100})
        
        created = 0
        for woo_coupon in woo_coupons:
            try:
                disc_type = 'percentage' if woo_coupon.get('discount_type') == 'percent' else 'fixed'
                amount = Decimal(str(woo_coupon.get('amount', 0)))
                
                WooCouponMap.objects.update_or_create(
                    woo_store=store,
                    woo_coupon_id=woo_coupon['id'],
                    defaults={
                        'coupon_code': woo_coupon.get('code', '').upper(),
                        'discount_type': disc_type,
                        'discount_value': amount,
                        'is_active': woo_coupon.get('individual_use', True),
                    }
                )
                created += 1
            except:
                pass
        
        store.last_sync_coupons = timezone.now()
        store.save(update_fields=['last_sync_coupons'])
        
        return {'created': created}
    
    # === SYNC ALL ===
    @classmethod
    def sync_store(cls, store: WooStore, full: bool = False) -> dict:
        """Sincronización completa de la tienda"""
        result = {}
        
        if store.sync_categories:
            result['categories'] = cls.sync_categories(store)
        
        if store.sync_products:
            result['products'] = cls.sync_products(store, full)
        
        if store.sync_customers:
            result['customers'] = cls.sync_customers(store)
        
        if store.sync_coupons:
            result['coupons'] = cls.sync_coupons(store)
        
        if store.sync_orders:
            result['orders'] = cls.sync_orders(store)
        
        return result
    
    # === WEBHOOK HANDLER ===
    @classmethod
    def handle_order_created(cls, store: WooStore, payload: dict) -> SaleOrder:
        """Procesa webhook de nueva orden"""
        woo_order = payload.get('order', {})
        
        # Check if already exists
        existing = WooOrderMap.objects.filter(
            woo_store=store, woo_order_id=woo_order['id']
        ).first()
        if existing:
            return existing.sale_order
        
        return cls._create_sale_order_from_woo(store, woo_order)
    
    @classmethod
    def handle_order_updated(cls, store: WooStore, payload: dict):
        """Procesa webhook de orden actualizada"""
        woo_order = payload.get('order', payload)
        woo_order_id = woo_order.get('id')
        
        mapping = WooOrderMap.objects.filter(
            woo_store=store, woo_order_id=woo_order_id
        ).first()
        
        if not mapping:
            return
        
        sale_order = mapping.sale_order
        woo_status = woo_order.get('status', '')
        status_map = store.get_status_map()
        sarix_status = status_map.get(woo_status, 'draft')
        
        from apps.sales.models import SaleOrderStatus
        if sarix_status == 'confirmed' and sale_order.status == SaleOrderStatus.DRAFT:
            from apps.sales.services import SaleOrderService
            SaleOrderService.confirm(sale_order, None)
        elif sarix_status == 'delivered' and sale_order.status == SaleOrderStatus.CONFIRMED:
            from apps.sales.services import SaleOrderService
            SaleOrderService.deliver(sale_order, None)
    
    @classmethod
    def handle_order_deleted(cls, store: WooStore, payload: dict):
        """Procesa webhook de orden eliminada"""
        woo_order_id = payload.get('id')
        
        mapping = WooOrderMap.objects.filter(
            woo_store=store, woo_order_id=woo_order_id
        ).first()
        
        if not mapping:
            return
        
        sale_order = mapping.sale_order
        from apps.sales.models import SaleOrderStatus
        sale_order.status = SaleOrderStatus.CANCELLED
        sale_order.save()
    
    @classmethod
    def handle_product_deleted(cls, store: WooStore, payload: dict):
        """Procesa webhook de producto eliminado"""
        woo_product_id = payload.get('id')
        
        mapping = WooProductMap.objects.filter(
            woo_store=store, woo_product_id=woo_product_id
        ).first()
        
        if mapping:
            if mapping.product_template:
                mapping.product_template.is_active = False
                mapping.product_template.save()
            if mapping.product:
                mapping.product.is_active = False
                mapping.product.save()
    
    # === CREATE WEBHOOKS IN WOOCOMMERCE ===
    @classmethod
    def create_webhooks(cls, store: WooStore) -> dict:
        """Crea webhooks en WooCommerce para recibir eventos"""
        from django.conf import settings
        
        client = cls.get_client(store)
        
        # Determinar URL base del webhook
        base_url = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
        webhook_url = f"https://{base_url}/api/woo/webhook/"
        
        topics = [
            'order.created',
            'order.updated', 
            'order.deleted',
            'product.created',
            'product.updated',
            'product.deleted',
            'customer.created',
            'customer.updated',
            'customer.deleted',
        ]
        
        created = []
        errors = []
        
        for topic in topics:
            try:
                webhook_data = {
                    'name': f'Sarix Sync - {topic}',
                    'topic': topic,
                    'delivery_url': webhook_url,
                    'secret': store.webhook_secret or '',
                    'status': 'active'
                }
                result = client.create_webhook(webhook_data)
                created.append({'topic': topic, 'id': result.get('id')})
            except Exception as e:
                errors.append({'topic': topic, 'error': str(e)})
        
        return {
            'created': created,
            'errors': errors,
            'webhook_url': webhook_url
        }
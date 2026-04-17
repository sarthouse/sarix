import hmac
import hashlib
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse

from .models import (
    WooStore, WooProductMap, WooCategoryMap,
    WooCustomerMap, WooOrderMap, WooCouponMap, WooTaxMapping,
    WooWebhookLog
)
from .serializers import (
    WooStoreSerializer, WooProductMapSerializer,
    WooCategoryMapSerializer, WooCustomerMapSerializer,
    WooOrderMapSerializer, WooCouponMapSerializer,
    WooTaxMappingSerializer, SyncResultSerializer,
    WooWebhookLogSerializer
)
from .services import WooSyncService, WooCommerceAPIError


class WooStoreViewSet(viewsets.ModelViewSet):
    """ViewSet para tiendas WooCommerce"""
    queryset = WooStore.objects.all()
    serializer_class = WooStoreSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def sync_all(self, request, pk=None):
        """Sincronización completa de la tienda"""
        store = self.get_object()
        try:
            full = request.data.get('full', False)
            result = WooSyncService.sync_store(store, full=full)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def sync_products(self, request, pk=None):
        """Sincroniza productos"""
        store = self.get_object()
        try:
            full = request.data.get('full', False)
            result = WooSyncService.sync_products(store, full=full)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_orders(self, request, pk=None):
        """Sincroniza órdenes"""
        store = self.get_object()
        try:
            status_filter = request.data.get('status', None)
            result = WooSyncService.sync_orders(store, status_filter=status_filter)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_categories(self, request, pk=None):
        """Sincroniza categorías"""
        store = self.get_object()
        try:
            result = WooSyncService.sync_categories(store)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_customers(self, request, pk=None):
        """Sincroniza clientes"""
        store = self.get_object()
        try:
            result = WooSyncService.sync_customers(store)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_coupons(self, request, pk=None):
        """Sincroniza cupones"""
        store = self.get_object()
        try:
            result = WooSyncService.sync_coupons(store)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WooProductMapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para mappings de productos"""
    queryset = WooProductMap.objects.all()
    serializer_class = WooProductMapSerializer


class WooCategoryMapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para mappings de categorías"""
    queryset = WooCategoryMap.objects.all()
    serializer_class = WooCategoryMapSerializer


class WooCustomerMapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para mappings de clientes"""
    queryset = WooCustomerMap.objects.all()
    serializer_class = WooCustomerMapSerializer


class WooOrderMapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para mappings de órdenes"""
    queryset = WooOrderMap.objects.all()
    serializer_class = WooOrderMapSerializer
    
    @action(detail=False, methods=['post'], url_path='import-order')
    def import_order(self, request):
        """Importa una orden específica por ID de WooCommerce"""
        store_id = request.data.get('store')
        order_id = request.data.get('order_id')
        
        if not store_id or not order_id:
            return Response(
                {'error': 'Se requiere store y order_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            store = WooStore.objects.get(id=store_id)
            client = WooSyncService.get_client(store)
            woo_order = client.get_order(order_id)
            
            sale_order = WooSyncService._create_sale_order_from_woo(store, woo_order)
            return Response({
                'success': True,
                'order_id': sale_order.id,
                'order_number': sale_order.number
            })
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WooCouponMapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para mappings de cupones"""
    queryset = WooCouponMap.objects.all()
    serializer_class = WooCouponMapSerializer


class WooTaxMappingViewSet(viewsets.ModelViewSet):
    """ViewSet para mappings de impuestos"""
    queryset = WooTaxMapping.objects.all()
    serializer_class = WooTaxMappingSerializer


class WooWebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para logs de webhooks"""
    queryset = WooWebhookLog.objects.all()
    serializer_class = WooWebhookLogSerializer
    permission_classes = [IsAuthenticated]


class WooWebhookReceiver(View):
    """Endpoint receptor de webhooks de WooCommerce"""
    permission_classes = [AllowAny]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        return self._handle_webhook(request)
    
    def _handle_webhook(self, request):
        topic = request.headers.get('X-WC-Webhook-Topic', '')
        delivery_id = request.headers.get('X-WC-Webhook-Delivery-ID', '')
        signature = request.headers.get('X-WC-Webhook-Signature', '')
        
        try:
            payload = json.loads(request.body)
        except:
            payload = {}
        
        store_url = payload.get('site_url') or request.headers.get('X-WC-Webhook-Source', '')
        
        if not store_url:
            return JsonResponse({'error': 'No se pudo identificar la tienda'}, status=400)
        
        store_url = store_url.rstrip('/')
        store = WooStore.objects.filter(url__startswith=store_url).first()
        
        if not store:
            WooWebhookLog.objects.create(
                store_id=0,
                topic=topic,
                delivery_id=delivery_id,
                payload=payload,
                success=False,
                error=f'Store no encontrado para URL: {store_url}'
            )
            return JsonResponse({'error': 'Store no encontrado'}, status=404)
        
        if store.webhook_secret:
            expected_signature = hmac.new(
                store.webhook_secret.encode('utf-8'),
                request.body,
                hashlib.sha256
            ).digest()
            if not hmac.compare_digest(signature.encode('utf-8') if signature else b'', expected_signature):
                WooWebhookLog.objects.create(
                    store=store,
                    topic=topic,
                    delivery_id=delivery_id,
                    payload=payload,
                    success=False,
                    error='Firma HMAC inválida'
                )
                return JsonResponse({'error': 'Firma inválida'}, status=401)
        
        try:
            self._process_webhook(store, topic, payload)
            
            WooWebhookLog.objects.create(
                store=store,
                topic=topic,
                delivery_id=delivery_id,
                payload=payload,
                success=True
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            WooWebhookLog.objects.create(
                store=store,
                topic=topic,
                delivery_id=delivery_id,
                payload=payload,
                success=False,
                error=str(e)
            )
            return JsonResponse({'error': str(e)}, status=500)
    
    def _process_webhook(self, store: WooStore, topic: str, payload: dict):
        """Procesa el webhook según el topic"""
        
        if topic.startswith('order.'):
            self._handle_order_webhook(store, topic, payload)
        elif topic.startswith('product.'):
            self._handle_product_webhook(store, topic, payload)
        elif topic.startswith('customer.'):
            self._handle_customer_webhook(store, topic, payload)
    
    def _handle_order_webhook(self, store: WooStore, topic: str, payload: dict):
        """Procesa webhooks de órdenes"""
        order_id = payload.get('id')
        
        if topic == 'order.created':
            WooSyncService.handle_order_created(store, payload)
        elif topic == 'order.updated':
            WooSyncService.handle_order_updated(store, payload)
        elif topic == 'order.deleted':
            WooSyncService.handle_order_deleted(store, payload)
    
    def _handle_product_webhook(self, store: WooStore, topic: str, payload: dict):
        """Procesa webhooks de productos"""
        product_id = payload.get('id')
        
        if topic == 'product.created':
            client = WooSyncService.get_client(store)
            WooSyncService._sync_single_product(store, payload, client)
        elif topic == 'product.updated':
            client = WooSyncService.get_client(store)
            WooSyncService._sync_single_product(store, payload, client)
        elif topic == 'product.deleted':
            WooSyncService.handle_product_deleted(store, payload)
    
    def _handle_customer_webhook(self, store: WooStore, topic: str, payload: dict):
        """Procesa webhooks de clientes"""
        customer_id = payload.get('id')
        
        if topic == 'customer.created':
            WooSyncService._sync_single_customer(store, payload)
        elif topic == 'customer.updated':
            WooSyncService._sync_single_customer(store, payload)


class WooWebhookManagementViewSet(viewsets.ViewSet):
    """ViewSet para gestionar webhooks en WooCommerce"""
    permission_classes = [IsAuthenticated]
    
    def list_webhooks(self, request, pk=None):
        """GET /webhooks/ - Listar webhooks de WooCommerce"""
        store_id = request.query_params.get('store')
        
        if not store_id:
            return Response({'error': 'Se requiere store'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            store = WooStore.objects.get(id=store_id)
            client = WooSyncService.get_client(store)
            webhooks = client.get_webhooks()
            return Response(webhooks)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def create_webhooks(self, request, pk=None):
        """POST /webhooks/create/ - Crear webhooks en WooCommerce"""
        store_id = request.data.get('store')
        
        if not store_id:
            return Response({'error': 'Se requiere store'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            store = WooStore.objects.get(id=store_id)
            result = WooSyncService.create_webhooks(store)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete_webhook(self, request, pk=None):
        """DELETE /webhooks/{id}/ - Eliminar webhook de WooCommerce"""
        store_id = request.data.get('store')
        webhook_id = pk
        
        if not store_id or not webhook_id:
            return Response({'error': 'Se requiere store y webhook_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            store = WooStore.objects.get(id=store_id)
            client = WooSyncService.get_client(store)
            result = client.delete_webhook(webhook_id)
            return Response(result)
        except WooCommerceAPIError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
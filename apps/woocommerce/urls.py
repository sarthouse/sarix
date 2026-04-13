from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WooStoreViewSet, WooProductMapViewSet, WooCategoryMapViewSet,
    WooCustomerMapViewSet, WooOrderMapViewSet, WooCouponMapViewSet,
    WooTaxMappingViewSet, WooWebhookLogViewSet,
    WooWebhookReceiver, WooWebhookManagementViewSet
)

router = DefaultRouter()
router.register(r'stores', WooStoreViewSet, basename='woo-store')
router.register(r'products', WooProductMapViewSet, basename='woo-product')
router.register(r'categories', WooCategoryMapViewSet, basename='woo-category')
router.register(r'customers', WooCustomerMapViewSet, basename='woo-customer')
router.register(r'orders', WooOrderMapViewSet, basename='woo-order')
router.register(r'coupons', WooCouponMapViewSet, basename='woo-coupon')
router.register(r'tax-mappings', WooTaxMappingViewSet, basename='woo-tax')
router.register(r'webhook-logs', WooWebhookLogViewSet, basename='woo-webhook-log')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint receptor de webhooks (sin autenticación)
    path('webhook/', WooWebhookReceiver.as_view(), name='woo-webhook-receiver'),
    # Gestión de webhooks en WooCommerce
    path('webhooks/', WooWebhookManagementViewSet.as_view({'get': 'list_webhooks', 'post': 'create_webhooks'}), name='woo-webhooks'),
]
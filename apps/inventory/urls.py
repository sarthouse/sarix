from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, AttributeViewSet,
    ProductTemplateViewSet, ProductViewSet,
    LotViewSet, StockQuantViewSet,
    WarehouseViewSet, StockViewSet,
    StockMovementViewSet, StockAlertViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'attributes', AttributeViewSet)
router.register(r'templates', ProductTemplateViewSet)
router.register(r'products', ProductViewSet)
router.register(r'lots', LotViewSet)
router.register(r'quants', StockQuantViewSet, basename='stock-quant')
router.register(r'warehouses', WarehouseViewSet)
router.register(r'stock', StockViewSet)
router.register(r'movements', StockMovementViewSet)
router.register(r'alerts', StockAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
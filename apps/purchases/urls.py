from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseOrderViewSet, PurchaseOrderPartnerLineViewSet

router = DefaultRouter()
router.register(r'orders', PurchaseOrderViewSet)
router.register(r'supplier-info', PurchaseOrderPartnerLineViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
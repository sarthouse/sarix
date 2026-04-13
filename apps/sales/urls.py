from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleOrderViewSet, SaleQuoteViewSet

router = DefaultRouter()
router.register(r'orders', SaleOrderViewSet)
router.register(r'quotes', SaleQuoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
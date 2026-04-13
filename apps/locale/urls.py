from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CountryViewSet, StateViewSet, CurrencyViewSet, CurrencyRateViewSet

router = DefaultRouter()
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'states', StateViewSet, basename='state')
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'currency-rates', CurrencyRateViewSet, basename='currency-rate')

urlpatterns = [
    path('', include(router.urls)),
]
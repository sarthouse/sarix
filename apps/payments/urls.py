from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, CheckViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'checks', CheckViewSet, basename='check')

urlpatterns = [
    path('', include(router.urls)),
]
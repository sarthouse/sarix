from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartnerViewSet, PartnerCategoryViewSet

router = DefaultRouter()
router.register(r'categories', PartnerCategoryViewSet, basename='partner-category')
router.register(r'', PartnerViewSet, basename='partner')

urlpatterns = [
    path('', include(router.urls)),
]
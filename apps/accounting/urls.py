from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentTypeViewSet, JournalViewSet

router = DefaultRouter()
router.register(r'document-types', DocumentTypeViewSet, basename='document-type')
router.register(r'journals', JournalViewSet, basename='journal')

urlpatterns = [
    path('', include(router.urls)),
]
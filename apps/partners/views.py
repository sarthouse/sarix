from rest_framework import generics, filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import Partner, PartnerCategory
from .serializers import (
    PartnerSerializer, PartnerListSerializer,
    PartnerCategorySerializer, PartnerCategoryListSerializer
)


class PartnerCategoryViewSet(viewsets.ModelViewSet):
    queryset = PartnerCategory.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'shortcut']

    def get_serializer_class(self):
        return PartnerCategoryListSerializer if self.action == 'list' else PartnerCategorySerializer


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.select_related('parent', 'state', 'country')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['partner_type', 'is_company', 'is_customer', 'is_supplier', 'iva_condition', 'state', 'country']
    search_fields = ['name', 'cuit', 'email', 'phone']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        return PartnerListSerializer if self.action == 'list' else PartnerSerializer
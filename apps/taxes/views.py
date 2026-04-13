from rest_framework import status, filters
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .models import Tax
from .serializers import TaxSerializer, TaxListSerializer


class TaxViewSet(ModelViewSet):
    queryset = Tax.objects.prefetch_related('children_taxes')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type_tax_use', 'tax_group', 'amount_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['sequence', 'name']

    def get_serializer_class(self):
        return TaxListSerializer if self.action == 'list' else TaxSerializer
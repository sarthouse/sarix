from rest_framework import status, filters
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, State, Currency, CurrencyRate
from .serializers import CountrySerializer, StateSerializer, CurrencySerializer, CurrencyRateSerializer


class CountryViewSet(ModelViewSet):
    queryset = Country.objects.prefetch_related('states')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'code_alpha3']
    ordering_fields = ['name', 'code']


class StateViewSet(ModelViewSet):
    queryset = State.objects.select_related('country')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['country', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']


class CurrencyViewSet(ModelViewSet):
    queryset = Currency.objects.prefetch_related('rates')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'is_company_currency']
    search_fields = ['name', 'code', 'symbol']
    ordering_fields = ['is_company_currency', 'name']


class CurrencyRateViewSet(ModelViewSet):
    queryset = CurrencyRate.objects.select_related('currency', 'company')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['currency', 'date', 'company']
    ordering_fields = ['-date']
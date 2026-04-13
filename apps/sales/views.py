from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .models import SaleOrder, SaleOrderStatus, SaleQuote, SaleQuoteStatus
from .serializers import (
    SaleOrderSerializer,
    SaleOrderListSerializer,
    SaleOrderCreateSerializer,
    SaleOrderLineSerializer,
    SaleQuoteSerializer,
    SaleQuoteListSerializer,
    SaleQuoteCreateSerializer,
    SaleQuoteLineSerializer
)
from .services import SaleOrderService, SaleQuoteService


class SaleOrderViewSet(ModelViewSet):
    queryset = SaleOrder.objects.select_related(
        'customer', 'warehouse', 'journal', 'created_by'
    ).prefetch_related('lines__product')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'customer', 'warehouse']
    search_fields = ['number', 'customer__name']
    ordering_fields = ['date', 'created_at', 'number']

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_is_customer = self.request.query_params.get('customer_is_customer')
        if customer_is_customer is not None:
            queryset = queryset.filter(customer__is_customer=customer_is_customer.lower() == 'true')
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return SaleOrderListSerializer
        if self.action == 'create':
            return SaleOrderCreateSerializer
        return SaleOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirma una orden y reserva stock."""
        order = self.get_object()

        try:
            SaleOrderService.confirm(order)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Entrega una orden (crea movements de salida)."""
        order = self.get_object()
        period_id = request.data.get('period_id')

        if not period_id:
            return Response(
                {'period_id': 'Requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            SaleOrderService.deliver(order, period_id)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def invoice(self, request, pk=None):
        """Factura una orden (crea journal de ingresos)."""
        order = self.get_object()
        period_id = request.data.get('period_id')

        if not period_id:
            return Response(
                {'period_id': 'Requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            SaleOrderService.invoice(order, period_id, request.data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela una orden."""
        order = self.get_object()

        try:
            SaleOrderService.cancel(order)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleOrderSerializer(order).data)

    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """Lista las lineas de una orden."""
        order = self.get_object()
        lines = order.lines.all()
        serializer = SaleOrderLineSerializer(lines, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != 'draft':
            return Response(
                {"detail": "Solo se pueden eliminar ordenes en borrador."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SaleQuoteViewSet(ModelViewSet):
    queryset = SaleQuote.objects.select_related(
        'customer', 'warehouse', 'sale_order', 'created_by'
    ).prefetch_related('lines__product')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'customer', 'warehouse']
    search_fields = ['number', 'customer__name']
    ordering_fields = ['date', 'created_at', 'number']

    def get_serializer_class(self):
        if self.action == 'list':
            return SaleQuoteListSerializer
        if self.action == 'create':
            return SaleQuoteCreateSerializer
        return SaleQuoteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        valid_only = self.request.query_params.get('valid_only')
        if valid_only and valid_only.lower() == 'true':
            from datetime import date
            queryset = queryset.filter(
                status=SaleQuoteStatus.BUDGET,
                valid_until__gte=date.today()
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Acepta un presupuesto y crea la orden de venta."""
        quote = self.get_object()

        try:
            order = SaleQuoteService.accept(quote)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleQuoteSerializer(quote).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechaza un presupuesto."""
        quote = self.get_object()

        try:
            SaleQuoteService.reject(quote)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleQuoteSerializer(quote).data)

    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """Lista las lineas de un presupuesto."""
        quote = self.get_object()
        lines = quote.lines.all()
        serializer = SaleQuoteLineSerializer(lines, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        quote = self.get_object()
        if quote.status != 'budget':
            return Response(
                {"detail": "Solo se pueden eliminar presupuestos en estado presupuesto."},
                status=status.HTTP_400_BAD_REQUEST
            )
        quote.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
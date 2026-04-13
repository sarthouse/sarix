from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .models import PurchaseOrder, PurchaseOrderStatus, PurchaseOrderPartnerLine
from .serializers import (
    PurchaseOrderSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderCreateSerializer,
    PurchaseOrderLineSerializer,
    PurchaseOrderPartnerLineSerializer,
    PurchaseOrderPartnerLineCreateSerializer
)


class PurchaseOrderViewSet(ModelViewSet):
    queryset = PurchaseOrder.objects.select_related(
        'partner', 'warehouse', 'currency', 'created_by'
    ).prefetch_related('lines', 'lines__product', 'lines__template', 'lines__taxes', 'picking_ids')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['state', 'partner', 'warehouse', 'currency']
    search_fields = ['name', 'partner__name', 'partner_ref']
    ordering_fields = ['date_order', 'created_at', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        partner_is_supplier = self.request.query_params.get('partner_is_supplier')
        if partner_is_supplier is not None:
            queryset = queryset.filter(partner__is_supplier=partner_is_supplier.lower() == 'true')
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirma el pedido de compra."""
        order = self.get_object()

        try:
            order.confirm()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela el pedido de compra."""
        order = self.get_object()

        try:
            order.cancel()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def draft(self, request, pk=None):
        """Devuelve el pedido a borrador."""
        order = self.get_object()

        try:
            order.draft()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        """Crea recepciones de stock para el pedido."""
        order = self.get_object()

        try:
            movements = order.action_restock()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': f'{len(movements)} recepción(es) creada(s)',
            'movements': [{'id': m.id, 'number': m.number} for m in movements]
        })

    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """Crea una factura de proveedor."""
        order = self.get_object()

        try:
            invoice = order.action_create_invoice()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': 'Factura creada',
            'invoice': {'id': invoice.id, 'number': invoice.number}
        })

    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """Obtiene las líneas del pedido."""
        order = self.get_object()
        lines = order.lines.all()
        serializer = PurchaseOrderLineSerializer(lines, many=True)
        return Response(serializer.data)


class PurchaseOrderPartnerLineViewSet(ModelViewSet):
    queryset = PurchaseOrderPartnerLine.objects.select_related(
        'partner', 'product_template', 'currency'
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['partner', 'product_template']
    search_fields = ['partner__name', 'product_template__sku', 'product_code']
    ordering_fields = ['partner__name', 'product_template__sku']

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderPartnerLineCreateSerializer
        return PurchaseOrderPartnerLineSerializer

    def perform_create(self, serializer):
        serializer.save()
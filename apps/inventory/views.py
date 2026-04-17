from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import (
    Category, Attribute, AttributeValue, UnitOfMeasure,
    ProductTemplate, Product, Lot, StockQuant,
    Warehouse, Stock, StockMovement, StockAlert
)
from .serializers import (
    CategorySerializer, AttributeSerializer, AttributeValueSerializer,
    ProductSerializer, ProductListSerializer,
    WarehouseSerializer, StockSerializer,
    StockMovementSerializer, StockMovementCreateSerializer,
    StockAlertSerializer, StockQuantSerializer, LotSerializer
)
from .services import StockMovementService, StockAlertService, StockQuantService

MOVEMENT_STATUS = [
    ('draft', 'Borrador'),
    ('posted', 'Publicado'),
    ('cancelled', 'Anulado'),
]


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class AttributeViewSet(ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductTemplateViewSet(ModelViewSet):
    queryset = ProductTemplate.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sku', 'name']
    ordering_fields = ['sku', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related('template').all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['sku', 'name']


class LotViewSet(ModelViewSet):
    queryset = Lot.objects.select_related('template', 'warehouse').all()
    serializer_class = LotSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['number']


class StockQuantViewSet(ModelViewSet):
    serializer_class = StockQuantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__sku', 'lot__number']
    
    def get_queryset(self):
        return StockQuant.objects.select_related(
            'product', 'product__template', 'warehouse', 'lot'
        )


class WarehouseViewSet(ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class StockViewSet(ModelViewSet):
    queryset = Stock.objects.select_related('template', 'product', 'warehouse').all()
    serializer_class = StockSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['template__sku', 'product__sku', 'warehouse__code']


class StockMovementViewSet(ModelViewSet):
    queryset = StockMovement.objects.select_related(
        'product', 'product__template', 'template', 'lot', 'warehouse_src', 'warehouse_dst', 'partner', 'journal'
    ).all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference', 'product__sku', 'template__sku']
    ordering_fields = ['created_at', 'qty']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return StockMovementCreateSerializer
        return StockMovementSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        movement = self.get_object()
        period_id = request.data.get('period_id')
        
        if not period_id:
            return Response({'period_id': 'Requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            StockMovementService.post(movement, period_id, request.data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(StockMovementSerializer(movement).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        movement = self.get_object()
        
        try:
            StockMovementService.cancel(movement)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(StockMovementSerializer(movement).data)

    def destroy(self, request, *args, **kwargs):
        movement = self.get_object()
        if movement.status != 'draft':
            return Response(
                {"detail": "Solo se pueden eliminar movimientos en borrador."},
                status=status.HTTP_400_BAD_REQUEST
            )
        movement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockAlertViewSet(ModelViewSet):
    queryset = StockAlert.objects.select_related('quant', 'stock').all()
    serializer_class = StockAlertSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        StockAlertService.resolve(alert)
        return Response(StockAlertSerializer(alert).data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.queryset.filter(resolved=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
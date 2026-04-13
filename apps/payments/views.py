from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Payment, PaymentLine, Check, CheckOperation, PaymentState, CheckState
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer,
    CheckSerializer, CheckCreateSerializer
)
from apps.payments.services import PaymentService


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirma el pago"""
        payment = self.get_object()
        try:
            PaymentService.confirm(payment)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def collect(self, request, pk=None):
        """Marca como cobrado/pagado"""
        payment = self.get_object()
        try:
            PaymentService.collect(payment)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Concilia el pago con las facturas"""
        payment = self.get_object()
        try:
            PaymentService.reconcile(payment)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela el pago"""
        payment = self.get_object()
        try:
            PaymentService.cancel(payment)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all()
    serializer_class = CheckSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CheckCreateSerializer
        return CheckSerializer
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Deposita el cheque"""
        check = self.get_object()
        try:
            PaymentService.deposit_check(check)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CheckSerializer(check).data)
    
    @action(detail=True, methods=['post'])
    def endorse(self, request, pk=None):
        """Endosa el cheque a un tercero"""
        partner_id = request.data.get('partner')
        check = self.get_object()
        try:
            PaymentService.endorse_check(check, partner_id)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CheckSerializer(check).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Marca el cheque como rechazado"""
        check = self.get_object()
        try:
            PaymentService.reject_check(check)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CheckSerializer(check).data)
    
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Entrega el cheque a un proveedor"""
        partner_id = request.data.get('partner')
        check = self.get_object()
        try:
            PaymentService.deliver_check(check, partner_id)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CheckSerializer(check).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela el cheque"""
        check = self.get_object()
        try:
            PaymentService.cancel_check(check)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CheckSerializer(check).data)
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .models import DocumentType, Journal, JournalStatus
from .serializers import DocumentTypeSerializer, JournalSerializer, JournalListSerializer


class DocumentTypeViewSet(ModelViewSet):
    queryset = DocumentType.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['document_class', 'iva_type', 'is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code']

    def get_serializer_class(self):
        return DocumentTypeSerializer


class JournalViewSet(ModelViewSet):
    queryset = Journal.objects.prefetch_related("lines__account")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "period", "partner"]
    search_fields = ["number", "description", "reference"]
    ordering_fields = ["date", "number"]

    def get_serializer_class(self):
        return JournalListSerializer if self.action == "list" else JournalSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        journal = self.get_object()
        if journal.status != JournalStatus.DRAFT:
            return Response(
                {"detail": "Solo se pueden eliminar asientos en borrador."},
                status=status.HTTP_400_BAD_REQUEST
            )
        journal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def post_journal(self, request, pk=None):
        journal = self.get_object()
        if journal.status != JournalStatus.DRAFT:
            return Response({"detail": "Solo se pueden contabilizar borradores."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            journal.post()
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(JournalSerializer(journal).data)
    
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        journal = self.get_object()
        if journal.status != JournalStatus.POSTED:
            return Response({"detail": "Solo se pueden anular asientos contabilizados."},
                            status=status.HTTP_400_BAD_REQUEST)
        reverse = Journal.objects.create(
            date=request.data.get("date", journal.date),
            description=f"Reversa de {journal.number}: {journal.description}",
            period=journal.period,
            created_by=request.user,
            reference=journal.number
        )
        for line in journal.lines.all():
            line.pk = None
            line.journal = reverse
            line.debit_amount, line.credit_amount = line.credit_amount, line.debit_amount
            line.save()
        reverse.post()
        journal.status = JournalStatus.CANCELLED
        journal.save()
        return Response(JournalSerializer(reverse).data)
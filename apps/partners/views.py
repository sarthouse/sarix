from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Partner
from .serializers import PartnerSerializer, PartnerListSerializer

class PartnerListCreateView(generics.ListCreateAPIView):
    queryset = Partner.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["partner_type"]
    search_fields = ["name", "cuit"]
    def get_serializer_class(self):
        return PartnerListSerializer if self.request.method == "GET" else PartnerSerializer

class PartnerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
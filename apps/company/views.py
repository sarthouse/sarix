from rest_framework import generics, permissions
from .models import Company
from .serializers import CompanySerializer

class CompanyView(generics.RetrieveUpdateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Company.get()

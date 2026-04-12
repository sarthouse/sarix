from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Account
from .serializers import AccountSerializer, AccountTreeSerializer

class AccountListCreateView(generics.ListCreateAPIView):
    queryset = Account.objects.filter(is_active=True)
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["account_type", "allows_movements", "parent"]

class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        if account.journalline_set.exists():
            return Response(
                {"detail": "No se puede eliminar una cuenta con movimientos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        account.is_active = False
        account.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AccountTreeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountTreeSerializer

    def get(self, request):
        roots = Account.objects.root_nodes().filter(is_active=True)
        return Response(AccountTreeSerializer(roots, many=True).data)
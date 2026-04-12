from django.urls import path
from .views import AccountListCreateView, AccountDetailView, AccountTreeView

urlpatterns = [
    path('', AccountListCreateView.as_view(), name='account-list'),
    path('tree/', AccountTreeView.as_view(), name='account-tree'),
    path('<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
]
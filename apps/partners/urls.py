from django.urls import path
from .views import PartnerListCreateView, PartnerDetailView

urlpatterns = [
    path("", PartnerListCreateView.as_view(), name="partner-list"),
    path("<int:pk>/", PartnerDetailView.as_view(), name="partner-detail"),
]
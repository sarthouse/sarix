from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),
    # Auth JWT
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API URLs
    path('api/v1/company/', include('apps.company.urls')),
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.accounting.urls')),
    path('api/v1/partners/', include('apps.partners.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

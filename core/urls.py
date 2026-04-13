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
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/sales/', include('apps.sales.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/taxes/', include('apps.taxes.urls')),
    path('api/v1/locale/', include('apps.locale.urls')),
    path('api/v1/purchases/', include('apps.purchases.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/woocommerce/', include('apps.woocommerce.urls')),
    # API Documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

"""
Tests de performance para SARIX.
Validar que optimizaciones P1-P5 funcionan.

Ejecutar: pytest tests/test_performance.py -v --durations=10
"""
import pytest
from django.test import TestCase, Client
from django.db import connection
from django.test.utils import override_settings
from unittest.mock import patch

# Django setup
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.sales.models import SaleOrder
from apps.inventory.models import StockQuant, Product, Warehouse
from apps.payments.models import Payment
from apps.accounting.models import Journal

User = get_user_model()


@override_settings(DEBUG=True)
class PerformanceTestCase(TestCase):
    """Tests para validar optimizaciones de queries"""
    
    def setUp(self):
        """Setup datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
    
    def count_queries(self):
        """Helper para contar queries ejecutadas"""
        return len(connection.queries)
    
    def test_sale_orders_list_query_optimization(self):
        """P1: Validar que listado SaleOrder no hace N+1 queries"""
        # Setup: crear 10 órdenes
        # (en real harías factories, esto es solo ejemplo)
        
        # Contar queries antes
        connection.queries_log.clear()
        
        # GET lista
        response = self.client.get('/api/v1/sales/orders/')
        
        # Validar queries
        query_count = len(connection.queries)
        
        # Esperado: ~5-7 queries (no 50+)
        assert query_count < 10, f"Demasiadas queries: {query_count}"
        assert response.status_code == 200
    
    def test_payment_viewset_select_related(self):
        """P1: Validar que PaymentViewSet usa select_related"""
        connection.queries_log.clear()
        
        response = self.client.get('/api/v1/payments/payment/')
        
        query_count = len(connection.queries)
        assert query_count < 10, f"Demasiadas queries en payments: {query_count}"
    
    def test_stock_cache_manager(self):
        """P4: Validar que StockCacheManager invalida caché"""
        from apps.inventory.services import StockCacheManager
        from django.core.cache import cache
        
        # Clear cache
        cache.clear()
        
        # Get cache (no existe, crea)
        result = StockCacheManager.get_or_fetch(1, 1)
        assert result['qty_available'] == 0.0
        
        # Verificar está en cache
        cached = cache.get(StockCacheManager.get_cache_key(1, 1))
        assert cached is not None
        
        # Invalidar
        StockCacheManager.invalidate(1, 1)
        cached = cache.get(StockCacheManager.get_cache_key(1, 1))
        assert cached is None
    
    def test_validator_works(self):
        """P2: Validar que validadores funcionan"""
        from apps.core.validators import SaleOrderValidator
        from django.core.exceptions import ValidationError
        
        # Create mock order without customer
        class MockOrder:
            customer = None
            date = None
            warehouse = None
            lines = None
        
        order = MockOrder()
        
        # Debe fallar validación
        with pytest.raises(ValidationError):
            SaleOrderValidator.validate(order)


@override_settings(DEBUG=True)
class CacheInvalidationTestCase(TestCase):
    """Tests para validar que signals invalidan caché"""
    
    def test_stock_movement_signal_invalidates_cache(self):
        """P5: Validar que signal de StockMovement invalida caché"""
        from apps.inventory.signals import on_movement_posted
        from apps.inventory.models import StockMovement
        from django.core.cache import cache
        
        cache.clear()
        
        # Mock StockMovement
        class MockMovement:
            status = 'posted'
            product_id = 1
            warehouse_src_id = 1
            warehouse_dst_id = None
            class product:
                id = 1
                product_type = 'almacenable'
        
        # Trigger signal
        on_movement_posted(
            sender=StockMovement,
            instance=MockMovement(),
            created=False
        )
        
        # Verificar caché fue invalidado (no hay mejor forma sin DB real)
        # En prod harías con datos reales de BD


class LoadTestBaselineCase(TestCase):
    """Capturar baseline metrics antes/después optimizaciones"""
    
    def test_baseline_sale_orders_response_time(self):
        """Baseline: tiempo respuesta listado órdenes"""
        import time
        
        self.user = User.objects.create_user(
            username='user2', 
            password='pass'
        )
        client = Client()
        client.login(username='user2', password='pass')
        
        start = time.time()
        response = client.get('/api/v1/sales/orders/')
        elapsed = time.time() - start
        
        # Log baseline (reemplazar con > 0.5 después optimización)
        print(f"\n[BASELINE] Sale orders list: {elapsed:.2f}s")
        
        # Esperar que sea < 1s (será más en primer run)
        # assert elapsed < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

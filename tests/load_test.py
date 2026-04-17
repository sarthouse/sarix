"""
Tests de carga con Locust.
Simula múltiples usuarios simultaneos con workloads realistas.

Uso: locust -f tests/load_test.py --host=http://localhost:8000 -c 10 -r 2 -t 60s
"""
from locust import HttpUser, task, between
import json
import random


class SARIXUser(HttpUser):
    """Usuario simulado navegando SARIX"""
    wait_time = between(1, 3)  # Espera 1-3 seg entre requests
    
    def on_start(self):
        """Login antes de empezar"""
        self.auth_header = {}
        # Obtener token JWT
        response = self.client.post(
            '/api/v1/auth/token/',
            json={'username': 'demo', 'password': 'demo'},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            self.auth_header = {'Authorization': f'Bearer {token}'}
    
    @task(5)
    def list_sale_orders(self):
        """Listar órdenes de venta (weight 5)"""
        with self.client.get(
            '/api/v1/sales/orders/',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(3)
    def list_stock_quant(self):
        """Listar stock disponible"""
        with self.client.get(
            '/api/v1/inventory/stock-quant/',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def list_payments(self):
        """Listar pagos"""
        with self.client.get(
            '/api/v1/payments/payment/',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def list_journals(self):
        """Listar asientos contables"""
        with self.client.get(
            '/api/v1/accounting/journal/',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def list_purchase_orders(self):
        """Listar órdenes de compra"""
        with self.client.get(
            '/api/v1/purchases/orders/',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def search_products(self):
        """Búsqueda de productos"""
        with self.client.get(
            '/api/v1/inventory/products/?search=test',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class AdminUser(HttpUser):
    """Admin usuario con más operaciones"""
    wait_time = between(2, 4)
    
    def on_start(self):
        """Login como admin"""
        self.auth_header = {}
        response = self.client.post(
            '/api/v1/auth/token/',
            json={'username': 'admin', 'password': 'admin'},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            self.auth_header = {'Authorization': f'Bearer {token}'}
    
    @task(3)
    def list_sale_orders_all(self):
        """Listar todas órdenes de venta"""
        with self.client.get(
            '/api/v1/sales/orders/?limit=100',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def filter_by_status(self):
        """Filtrar por estado"""
        with self.client.get(
            '/api/v1/sales/orders/?status=confirmed',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def report_balance(self):
        """Generar reporte de balance"""
        with self.client.get(
            '/api/v1/accounting/balance/',
            headers=self.auth_header,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

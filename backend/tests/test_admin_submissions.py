from unittest.mock import patch
import unittest
from copy import deepcopy
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.core.permissions import ROLE_PERMISSIONS
from app.api.v1.endpoints.orders import service as orders
from app.api.v1.endpoints.quotes import service as quotes


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class AdminSubmissionsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user = {'id': 'client-test', 'role': 'cliente', 'permissions': ROLE_PERMISSIONS['cliente']}
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.addCleanup(app.dependency_overrides.clear)
        for service in (orders, quotes):
            self.addCleanup(setattr, service, '_data', service._data)
            self.addCleanup(setattr, service, '_counter', service._counter)
            service._data = deepcopy(service._data)

    def test_customer_orders_and_quotes_appear_to_admin_but_not_other_customer(self):
        person = {'customer_name': 'Solicitud prueba', 'customer_phone': '3001234567'}
        order = self.client.post('/api/v1/orders/', json={**person, 'address': 'Direccion de prueba',
            'subtotal': 10000, 'shipping_cost': 5000, 'total': 15000,
            'items': [{'product_id': 'prod-1', 'quantity': 1, 'unit_price': 10000, 'subtotal': 10000}]})
        quote = self.client.post('/api/v1/quotes/', json={**person,
            'items': [{'product_id': 'prod-1', 'quantity': 2, 'reference_price': 10000}]})
        self.assertEqual(order.status_code, 201)
        self.assertEqual(quote.status_code, 201)
        for role, user_id, visible in [('admin', 'admin-test', True), ('cliente', 'different-client', False), ('cliente', 'client-test', True)]:
            self.user.update(id=user_id, role=role, permissions=ROLE_PERMISSIONS[role])
            for path, created in [('orders', order.json()), ('quotes', quote.json())]:
                response = self.client.get('/api/v1/' + path + '/')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(any(item['id'] == created['id'] for item in response.json()), visible)

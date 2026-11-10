from unittest.mock import patch
import unittest
from copy import deepcopy
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.services.order_service import order_service
from app.core.permissions import ROLE_PERMISSIONS


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class OrderTrackingTests(unittest.TestCase):
    def setUp(self):
        saved_data, saved_counter = order_service._data, order_service._counter
        order_service._data = deepcopy(saved_data)
        self.addCleanup(setattr, order_service, '_data', saved_data)
        self.addCleanup(setattr, order_service, '_counter', saved_counter)
        self.user = {'id': 'test-owner', 'role': 'cliente', 'permissions': ROLE_PERMISSIONS['cliente']}
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)

    def test_created_order_can_be_tracked_and_updated_without_exposing_other_customers(self):
        response = self.client.post('/api/v1/orders/', json={
            'customer_name': 'Prueba', 'customer_phone': '3001234567', 'address': 'Direccion de prueba',
            'payment_method': 'contraentrega', 'subtotal': 10000, 'shipping_cost': 5000, 'total': 15000,
            'items': [{'product_id': 'prod-1', 'quantity': 1, 'unit_price': 10000, 'subtotal': 10000}]})
        self.assertEqual(response.status_code, 201)
        order = response.json()
        path = '/api/v1/tracking/' + order['order_number']
        result = self.client.get(path)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['id'], order['id'])
        self.user['id'] = 'other-customer'
        self.assertEqual(self.client.get(path).status_code, 404)
        self.user.update(role='admin', permissions=ROLE_PERMISSIONS['admin'])
        updated = self.client.patch('/api/v1/orders/' + order['id'] + '/status', json={'status': 'confirmado'})
        self.assertEqual(updated.status_code, 200)
        self.user.update(id='test-owner', role='cliente', permissions=ROLE_PERMISSIONS['cliente'])
        self.assertEqual(self.client.get(path).json()['order_status'], 'confirmado')

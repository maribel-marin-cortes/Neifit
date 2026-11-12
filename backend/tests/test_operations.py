import unittest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v1.endpoints.operations import router
from app.core.security import get_current_user
from app.services.delivery_service import DeliveryRequestCreate, delivery_service

OWNER = '11111111-1111-4111-8111-111111111111'
TARGET = '22222222-2222-4222-8222-222222222222'


class OperationsAccessTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.app.dependency_overrides[get_current_user] = lambda: {'id': OWNER, 'role': 'cliente', 'permissions': ['profile.read']}
        self.client = TestClient(self.app)

    @patch('app.api.v1.endpoints.operations.db.rpc', new_callable=AsyncMock)
    def test_client_cannot_respond_or_confirm_cash(self, rpc):
        self.assertEqual(self.client.post('/orders/' + TARGET + '/cash-receipt', json={'amount': '10000', 'reference': 'REC-001', 'confirmed_received': True}).status_code, 403)
        self.assertEqual(self.client.post('/quotes/' + TARGET + '/response', json={'total': '10000', 'conditions': 'Incluye domicilio', 'valid_until': '2030-01-01T12:00:00Z'}).status_code, 403)
        rpc.assert_not_awaited()

    @patch('app.api.v1.endpoints.operations.db.request', new_callable=AsyncMock)
    def test_notification_update_is_owner_scoped(self, request):
        response = self.client.patch('/notifications/' + TARGET + '/read')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.call_args.kwargs['params']['usuario_id'], 'eq.' + OWNER)

    @patch('app.api.v1.endpoints.operations.db.rpc', new_callable=AsyncMock)
    def test_admin_must_confirm_actual_cash_received(self, rpc):
        self.app.dependency_overrides[get_current_user] = lambda: {'id': OWNER, 'role': 'admin', 'permissions': []}
        response = self.client.post('/orders/' + TARGET + '/cash-receipt', json={'amount': '10000', 'reference': 'REC-001', 'confirmed_received': False})
        self.assertEqual(response.status_code, 422)
        rpc.assert_not_awaited()

    @patch('app.api.v1.endpoints.operations.delivery_service.approve_request', new_callable=AsyncMock)
    def test_only_users_manager_can_approve_delivery_request(self, approve):
        self.app.dependency_overrides[get_current_user] = lambda: {
            'id': OWNER, 'role': 'vendedor', 'permissions': ['orders.manage']}
        response = self.client.post('/solicitudes-mensajeria/' + TARGET + '/aprobar')
        self.assertEqual(response.status_code, 403)
        approve.assert_not_awaited()

    @patch('app.api.v1.endpoints.operations.delivery_service.approve_request', new_callable=AsyncMock)
    def test_users_manager_can_approve_delivery_request(self, approve):
        approve.return_value = {'id': TARGET, 'status': 'aprobado'}
        self.app.dependency_overrides[get_current_user] = lambda: {
            'id': OWNER, 'role': 'admin', 'permissions': ['users.manage']}
        response = self.client.post('/solicitudes-mensajeria/' + TARGET + '/aprobar')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'aprobado')


class DeliveryRequestValidationTests(unittest.TestCase):
    def valid(self):
        return dict(full_name='Persona Mensajera', email='persona@example.com', phone='3001234567',
                    document_id='12345678', vehicle_type='moto', vehicle_plate='ABC12D',
                    city='Medellín', password='Segura123!', notes='Disponible en las tardes')

    def test_rejects_weak_password_invalid_email_and_motor_vehicle_without_plate(self):
        from pydantic import ValidationError
        for change in ({'password': '123456'}, {'email': 'incorrecto'}, {'vehicle_plate': ''}):
            with self.assertRaises(ValidationError):
                DeliveryRequestCreate(**{**self.valid(), **change})

import unittest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v1.endpoints.account import router, own_profile

OWNER = '11111111-1111-4111-8111-111111111111'
ADDRESS = '22222222-2222-4222-8222-222222222222'


class AccountSecurityTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router, prefix='/account')
        app.dependency_overrides[own_profile] = lambda: {'id': OWNER, 'role': 'cliente'}
        self.client = TestClient(app)

    @patch('app.api.v1.endpoints.account.db.request', new_callable=AsyncMock)
    def test_cannot_edit_role_or_owner(self, request):
        for extra in [{'role': 'admin'}, {'user_id': ADDRESS}, {'email': 'other@example.com'}]:
            response = self.client.patch('/account', json={'full_name': 'Nombre cliente', 'phone': '3000000000', **extra})
            self.assertEqual(response.status_code, 422)
        request.assert_not_awaited()

    @patch('app.api.v1.endpoints.account.db.request', new_callable=AsyncMock)
    def test_address_of_other_owner_is_not_deleted(self, request):
        request.return_value = []
        response = self.client.delete('/account/addresses/' + ADDRESS)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(request.call_args.kwargs['params'], {'id': 'eq.' + ADDRESS, 'usuario_id': 'eq.' + OWNER})

    @patch('app.api.v1.endpoints.account.db.request', new_callable=AsyncMock)
    def test_create_uses_authenticated_owner(self, request):
        data = {'label': 'Casa', 'recipient': 'Nombre cliente', 'phone': '3000000000', 'address': 'Calle 10 # 20-30', 'city': 'Medellín', 'notes': ''}
        request.return_value = [{**data, 'id': ADDRESS}]
        self.assertEqual(self.client.post('/account/addresses', json=data).status_code, 201)
        self.assertEqual(request.call_args.kwargs['data']['usuario_id'], OWNER)
        self.assertEqual(self.client.post('/account/addresses', json={**data, 'user_id': ADDRESS}).status_code, 422)

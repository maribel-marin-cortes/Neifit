from unittest.mock import patch
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.core.permissions import ROLE_PERMISSIONS, project_order
from app.services.access_service import AccessService
from app.api.v1.endpoints.access import NewUser

ACTOR = '00000000-0000-4000-8000-000000000001'
CREATED = '00000000-0000-4000-8000-000000000002'
PERSON = dict(full_name='Persona prueba', email='prueba@example.com', phone='3001234567', password='Prueba12345!', role='mensajeria', email_verified_by_admin=True)


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class UserManagementApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user = {'id': ACTOR, 'role': 'admin', 'permissions': ROLE_PERMISSIONS['admin']}
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.addCleanup(app.dependency_overrides.clear)

    def test_customer_and_custom_role_cannot_create_users_even_with_forged_permissions(self):
        for role in ['cliente', 'auxiliar']:
            self.user['role'] = role
            self.assertEqual(self.client.post('/api/v1/access/users', json=PERSON).status_code, 403)
            self.assertEqual(self.client.post('/api/v1/access/roles', json={'code': 'auxiliar', 'name': 'Auxiliar', 'permissions': ['profile.read']}).status_code, 403)

    def test_create_user_keeps_admin_identity_and_does_not_return_password(self):
        with patch('app.api.v1.endpoints.access.access_service.create_user', AsyncMock(return_value={'id': CREATED, 'role': 'mensajeria'})) as create:
            result = self.client.post('/api/v1/access/users', json=PERSON)
            self.assertEqual(result.status_code, 201)
            self.assertNotIn('password', result.json())
            self.assertEqual(create.call_args.args[1], ACTOR)

    def test_registration_requires_email_verification_and_valid_fields(self):
        for change in [{'password': '123'}, {'email': 'invalid'}, {'email_verified_by_admin': False}, {'role': '../admin'}, {'full_name': '   '}]:
            self.assertEqual(self.client.post('/api/v1/access/users', json={**PERSON, **change}).status_code, 422)

    def test_custom_role_rejects_privilege_management_and_reserved_names(self):
        for code, permissions in [('auxiliar', ['profile.read', 'users.manage']), ('auxiliar', ['profile.read', 'access.manage']), ('admin', ['profile.read']), ('auxiliar', ['catalog.read'])]:
            response = self.client.post('/api/v1/access/roles', json={'code': code, 'name': 'Auxiliar', 'permissions': permissions})
            self.assertEqual(response.status_code, 403)

    def test_create_custom_role_uses_audited_rpc_with_server_actor(self):
        with patch('app.api.v1.endpoints.access.access_service.request', AsyncMock()) as rpc:
            response = self.client.post('/api/v1/access/roles', json={'code': 'auxiliar', 'name': 'Auxiliar', 'permissions': ['profile.read', 'products.manage']})
            self.assertEqual(response.status_code, 201)
            self.assertEqual(rpc.call_args.kwargs['json']['p_actor_id'], ACTOR)

    def test_custom_inventory_role_can_read_products_but_not_manage_users(self):
        self.user.update(role='auxiliar', permissions=['profile.read', 'products.manage'])
        self.assertEqual(self.client.get('/api/v1/products/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/access/').status_code, 403)

    def test_combined_customer_courier_role_cannot_read_assigned_order_financials(self):
        user = {'id': ACTOR, 'permissions': ['orders.read_own', 'delivery.read_assigned']}
        order = {'user_id': CREATED, 'assigned_delivery_user_id': ACTOR, 'total': 5000, 'items': []}
        self.assertNotIn('total', project_order(user, order))
        order['user_id'] = ACTOR
        self.assertEqual(project_order(user, order)['total'], 5000)


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class RegistrationServiceTests(unittest.IsolatedAsyncioTestCase):
    def response(self, status, data=None):
        return httpx.Response(status, json=data or {}, request=httpx.Request('POST', 'https://example.com/auth/v1/admin/users'))

    async def run_registration(self, rpc_error=None, activation_error=False):
        service = AccessService()
        transport = AsyncMock()
        transport.post.return_value = self.response(200, {'id': CREATED})
        transport.put.return_value = self.response(503 if activation_error else 200)
        transport.delete.return_value = self.response(200)
        async def request(method, path, **kwargs):
            if method == 'GET': return [{'code': 'mensajeria'}]
            if rpc_error: raise rpc_error
        with patch.object(service, 'request', AsyncMock(side_effect=request)), patch('app.services.access_service.httpx.AsyncClient') as client:
            client.return_value.__aenter__.return_value = transport
            try:
                result = await service.create_user(NewUser(**PERSON), ACTOR)
            except HTTPException as error:
                result = error
        return result, transport

    async def test_auth_account_is_blocked_until_role_assignment_and_never_exposes_password(self):
        result, transport = await self.run_registration()
        self.assertEqual(result['id'], CREATED)
        self.assertNotIn('password', result)
        self.assertEqual(transport.post.call_args.kwargs['json']['ban_duration'], '876000h')
        self.assertEqual(transport.put.call_args.kwargs['json'], {'ban_duration': 'none'})
        transport.delete.assert_not_called()

    async def test_failed_role_assignment_removes_only_just_created_identity(self):
        result, transport = await self.run_registration(HTTPException(status_code=403))
        self.assertEqual(result.status_code, 403)
        self.assertTrue(transport.delete.call_args.args[0].endswith('/' + CREATED))
        transport.put.assert_not_called()

    async def test_failed_activation_removes_incomplete_identity(self):
        result, transport = await self.run_registration(activation_error=True)
        self.assertEqual(result.status_code, 503)
        transport.delete.assert_called_once()

    async def test_custom_role_reads_granted_permissions_without_fixed_role_filter(self):
        service = AccessService()
        with patch.object(service, 'request', AsyncMock(return_value=[{'permission_code': 'products.manage'}, {'permission_code': 'users.manage'}])):
            self.assertEqual(await service.permissions_for_role('auxiliar'), ['products.manage'])

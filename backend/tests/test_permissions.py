from unittest.mock import patch
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.core.config import settings
from app.core.permissions import ROLE_PERMISSIONS
from app.services.order_service import OrderService
from app.schemas.order import OrderStatusUpdate
from app.services.access_service import AccessService


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class PermissionApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user = {'id': '00000000-0000-4000-8000-000000000001', 'role': 'cliente', 'permissions': ROLE_PERMISSIONS['cliente']}
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.addCleanup(app.dependency_overrides.clear)

    def test_courier_cannot_access_catalog_quotes_or_create_orders(self):
        self.user.update(role='mensajeria', permissions=ROLE_PERMISSIONS['mensajeria'])
        for path in ['/products/', '/categories/', '/quotes/', '/access/']:
            self.assertEqual(self.client.get('/api/v1' + path).status_code, 403, path)
        self.assertEqual(self.client.post('/api/v1/orders/', json={}).status_code, 403)
        self.assertEqual(self.client.post('/api/v1/quotes/', json={}).status_code, 403)

    def test_removed_permission_is_not_replaced_by_role_default(self):
        self.user['permissions'] = ['profile.read']
        self.assertEqual(self.client.get('/api/v1/products/').status_code, 403)
        self.assertEqual(self.client.get('/api/v1/orders/').status_code, 403)

    def test_customer_cannot_change_roles(self):
        response = self.client.patch('/api/v1/access/users/00000000-0000-4000-8000-000000000002/role', json={'role': 'admin'})
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_change_self_or_grant_excess_permissions(self):
        self.user.update(role='admin', permissions=ROLE_PERMISSIONS['admin'])
        self.assertEqual(self.client.patch('/api/v1/access/users/' + self.user['id'] + '/role', json={'role': 'cliente'}).status_code, 403)
        self.assertEqual(self.client.put('/api/v1/access/roles/mensajeria/permissions', json={'permissions': ['profile.read', 'products.manage']}).status_code, 403)
        self.assertEqual(self.client.put('/api/v1/access/roles/admin/permissions', json={'permissions': []}).status_code, 403)

    def test_permission_and_role_changes_use_server_identity(self):
        self.user.update(role='admin', permissions=ROLE_PERMISSIONS['admin'])
        with patch('app.api.v1.endpoints.access.access_service.request', new_callable=AsyncMock) as rpc:
            response = self.client.put('/api/v1/access/roles/mensajeria/permissions', json={'permissions': ['profile.read', 'delivery.read_assigned']})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(rpc.call_args.kwargs['json']['p_actor_id'], self.user['id'])
            response = self.client.patch('/api/v1/access/users/00000000-0000-4000-8000-000000000002/role', json={'role': 'mensajeria'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(rpc.call_args.kwargs['json']['p_role'], 'mensajeria')


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class DeliveryPermissionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = OrderService()
        self.service._data = deepcopy(self.service._data)
        self.user = {'id': 'usr-delivery-1', 'role': 'mensajeria', 'permissions': list(ROLE_PERMISSIONS['mensajeria'])}

    async def test_assigned_orders_have_only_logistics(self):
        orders = await self.service.list_for_user(self.user)
        self.assertTrue(orders)
        for order in orders:
            self.assertEqual(order['assigned_delivery_user_id'], self.user['id'])
            for key in ['customer_email', 'total', 'subtotal', 'payment_status', 'payment_method']:
                self.assertNotIn(key, order)
            self.assertNotIn('unit_price', order['items'][0])

    async def test_courier_cannot_read_or_change_unassigned_order(self):
        self.user['id'] = 'different-courier'
        self.assertIsNone(await self.service.get_by_id('ord-101', self.user))
        with self.assertRaises(HTTPException) as error:
            await self.service.update_status('ord-101', OrderStatusUpdate(status='entregado'), self.user)
        self.assertEqual(error.exception.status_code, 404)

    async def test_specific_action_permission_and_status_transitions(self):
        with self.assertRaises(HTTPException) as error:
            await self.service.update_status('ord-101', OrderStatusUpdate(status='cancelado'), self.user)
        self.assertEqual(error.exception.status_code, 403)
        self.user['permissions'].remove('delivery.complete')
        with self.assertRaises(HTTPException) as error:
            await self.service.update_status('ord-101', OrderStatusUpdate(status='entregado'), self.user)
        self.assertEqual(error.exception.status_code, 403)
        self.user['permissions'].append('delivery.complete')
        updated = await self.service.update_status('ord-101', OrderStatusUpdate(status='entregado'), self.user)
        self.assertEqual(updated['order_status'], 'entregado')
        self.assertNotIn('total', updated)
        with self.assertRaises(HTTPException) as error:
            await self.service.update_status('ord-101', OrderStatusUpdate(status='novedad'), self.user)
        self.assertEqual(error.exception.status_code, 409)


@patch.multiple('app.core.supabase_rest.settings', SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='')
class AccessLookupTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_database_permissions_do_not_restore_defaults(self):
        service = AccessService()
        with patch.object(service, 'request', AsyncMock(return_value=[])):
            self.assertEqual(await service.permissions_for_role('cliente'), [])

    async def test_database_failure_does_not_restore_defaults(self):
        service = AccessService()
        with patch.object(service, 'request', AsyncMock(side_effect=HTTPException(status_code=503))):
            with self.assertRaises(HTTPException) as error:
                await service.permissions_for_role('mensajeria')
            self.assertEqual(error.exception.status_code, 503)

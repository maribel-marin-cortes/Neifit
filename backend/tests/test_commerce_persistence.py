import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import httpx
from fastapi import HTTPException
from app.core.supabase_rest import SupabaseRest, uuid_value
from app.services.commerce_repository import CommerceRepository
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.quote_service import QuoteService
from app.schemas.order import OrderCreate


class SupabaseTransportTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, status, body):
        rest=SupabaseRest()
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(status,json=body))) as client:
            rest.client=client
            with patch('app.core.supabase_rest.settings',SimpleNamespace(SUPABASE_URL='https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY='server-test-key')):
                return await rest.request('POST','rpc/test',data={'p_actor':'test'})

    async def test_database_errors_never_return_success_or_private_key(self):
        for db_code,status in [('42501',403),('P0002',404),('P0001',409),('23505',409),('23503',422),('23514',422),('PGRST202',503)]:
            with self.assertRaises(HTTPException) as error:
                await self.call(400,{'code':db_code,'message':'Operación rechazada'})
            self.assertEqual(error.exception.status_code,status)
            self.assertNotIn('server-test-key',str(error.exception.detail))

    async def test_empty_database_stays_empty(self):
        self.assertEqual(await self.call(200,[]),[])

    async def test_network_errors_are_service_errors(self):
        rest=SupabaseRest();rest.client=SimpleNamespace(request=AsyncMock(side_effect=httpx.ConnectError('offline')))
        with patch('app.core.supabase_rest.settings',SimpleNamespace(SUPABASE_URL='https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY='test')):
            with self.assertRaises(HTTPException) as error:await rest.request('POST','rpc/test')
        self.assertEqual(error.exception.status_code,503)


class CommerceRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_products_use_real_categories_and_effective_stock(self):
        repo=CommerceRepository()
        rows=[{'id':str(uuid4()),'name':'Postre real','description':'','category_id':str(uuid4()),'is_active':True,'is_available':True,'stock':0,
               'categories':{'name':'Postres','slug':'postres','is_active':True}}]
        with patch('app.services.commerce_repository.db.rows',AsyncMock(return_value=rows)):
            result=await repo.products()
        self.assertFalse(result[0]['is_available']);self.assertTrue(result[0]['sales_enabled'])
        self.assertEqual(result[0]['category_name'],'Postres')

    async def test_owner_identity_is_not_taken_from_posted_payload(self):
        owner=str(uuid4());pid=str(uuid4());key=uuid4()
        data=OrderCreate(request_id=key,user_id=str(uuid4()),customer_name='Prueba cliente',customer_phone='3001234567',address='Direccion prueba',
                         items=[{'product_id':pid,'quantity':1}],total=1)
        with patch('app.services.commerce_repository.db.rpc',AsyncMock(return_value={'id':'saved'})) as rpc:
            result=await CommerceRepository().create_document('order',data,{'id':owner})
        self.assertEqual(result,{'id':'saved'})
        self.assertEqual(rpc.call_args.kwargs['p_actor'],owner)
        self.assertEqual(rpc.call_args.kwargs['p_request'],str(key))
        self.assertNotIn('user_id',rpc.call_args.kwargs['p_data'])

    async def test_demo_product_ids_are_rejected_before_any_write(self):
        data=OrderCreate(customer_name='Cliente',customer_phone='3001234567',address='Direccion prueba',items=[{'product_id':'prod-1','quantity':1}])
        with patch('app.services.commerce_repository.db.rpc',AsyncMock()) as rpc:
            with self.assertRaises(HTTPException):await CommerceRepository().create_document('order',data,{'id':str(uuid4())})
            rpc.assert_not_called()

    async def test_delivery_result_strips_prices_even_for_combined_role(self):
        row={'id':str(uuid4()),'user_id':'other','assigned_delivery_user_id':'courier','total':10000,'payment_status':'pendiente',
             'items':[{'product_name':'Prueba','quantity':1,'unit_price':10000}]}
        user={'id':'courier','permissions':['orders.read_own','delivery.read_assigned']}
        with patch('app.services.commerce_repository.db.rpc',AsyncMock(return_value=[row])):
            result=await CommerceRepository().orders(user)
        self.assertNotIn('total',result[0]);self.assertNotIn('unit_price',result[0]['items'][0])

    async def test_configured_services_do_not_fall_back_to_demo_after_failure(self):
        with patch('app.core.supabase_rest.settings',SimpleNamespace(SUPABASE_URL='https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY='test')):
            with patch('app.services.commerce_repository.db.rows',AsyncMock(side_effect=HTTPException(status_code=503))):
                with self.assertRaises(HTTPException):await ProductService().list_products()
            with patch('app.services.commerce_repository.db.rpc',AsyncMock(side_effect=HTTPException(status_code=503))):
                with self.assertRaises(HTTPException):await QuoteService().list_for_user({'id':'test'})
                with self.assertRaises(HTTPException):await OrderService().list_for_user({'id':'test'})

    async def test_product_deletion_is_deactivation(self):
        pid=str(uuid4())
        with patch('app.services.commerce_repository.db.rpc',AsyncMock()) as rpc:
            await CommerceRepository().deactivate_product(pid,{'id':str(uuid4())})
        self.assertEqual(rpc.call_args.kwargs['p_data'],{'is_active':False,'is_available':False})

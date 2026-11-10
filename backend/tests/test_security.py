import unittest
from unittest.mock import AsyncMock, patch, Mock

import httpx
import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.core import security
from app.core.config import Settings


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.config = Settings(_env_file=None, SUPABASE_URL="", SUPABASE_JWKS_URL="",
                               SUPABASE_JWT_ISSUER="", SUPABASE_SERVICE_ROLE_KEY="")
        self.override = patch.object(security, "settings", self.config)
        self.override.start()
        self.addCleanup(self.override.stop)
        self.client = TestClient(app)

    def request(self, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.put('/api/v1/site/content', json={}, headers=headers)

    def configure_supabase(self):
        self.config.SUPABASE_URL = 'https://example.supabase.co'
        self.config.SUPABASE_JWKS_URL = 'https://example.supabase.co/auth/v1/.well-known/jwks.json'
        self.config.SUPABASE_JWT_ISSUER = 'https://example.supabase.co/auth/v1'
        self.config.SUPABASE_SERVICE_ROLE_KEY = 'test-key'

    def test_anonymous_denied_and_public_content_readable(self):
        self.assertEqual(self.request().status_code, 401)
        self.assertEqual(self.client.get('/api/v1/site/content').status_code, 200)

    def test_demo_disabled_by_default(self):
        self.assertEqual(self.request('demo-token-admin').status_code, 401)

    def test_commercial_modules_require_authentication(self):
        for path in ['/products/', '/products/postre-de-maracuya-saludable', '/categories/', '/tracking/NF-2026-001', '/orders/', '/quotes/']:
            self.assertEqual(self.client.get('/api/v1' + path).status_code, 401, path)

    def test_public_landing_exposes_only_a_limited_preview(self):
        response = self.client.get('/api/v1/site/featured-products')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()), 3)
        self.assertGreater(len(response.json()), 0)
        self.assertNotIn('stock', response.json()[0])
        self.assertEqual(self.client.get('/api/v1/site/categories').status_code, 200)

    def test_authenticated_catalogue_and_private_tracking(self):
        self.config.ENABLE_DEMO_AUTH = True
        client_headers = {'Authorization': 'Bearer demo-token-cliente'}
        self.assertEqual(self.client.get('/api/v1/products/', headers=client_headers).status_code, 200)
        self.assertEqual(self.client.get('/api/v1/tracking/NF-2026-001', headers=client_headers).status_code, 200)
        self.assertEqual(self.client.get('/api/v1/tracking/NF-2026-002', headers=client_headers).status_code, 404)

    def test_explicit_local_demo_roles(self):
        self.config.ENABLE_DEMO_AUTH = True
        self.assertEqual(self.request('demo-token-admin').status_code, 200)
        for role in ('cliente', 'mensajeria'):
            self.assertEqual(self.request(f'demo-token-{role}').status_code, 403)

    def test_demo_blocked_in_production_or_with_supabase(self):
        self.config.ENABLE_DEMO_AUTH = True
        self.config.APP_ENV = 'production'
        self.assertEqual(self.request('demo-token-admin').status_code, 401)
        self.config.APP_ENV = 'development'
        self.configure_supabase()
        self.assertEqual(self.request('demo-token-admin').status_code, 401)

    def test_unconfigured_auth_fails_closed(self):
        self.assertEqual(self.request('unknown').status_code, 503)

    def test_current_profile_requires_auth(self):
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)
        self.config.ENABLE_DEMO_AUTH = True
        response = self.client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer demo-token-cliente'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], 'cliente')

    def test_current_profile_uses_supabase_profile(self):
        self.configure_supabase()
        uid = 'f110bb54-d8cb-41dc-ae24-040a1a0b8751'
        with patch.object(security, 'decode_token', return_value={'sub': uid}), patch.object(
            security, 'load_profile', AsyncMock(return_value={'id': uid, 'role': 'cliente'})
        ):
            response = self.client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer signed-token'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['id'], uid)

    def test_user_metadata_cannot_grant_admin(self):
        self.configure_supabase()
        payload = {'sub': 'f110bb54-d8cb-41dc-ae24-040a1a0b8751',
                   'user_metadata': {'role': 'admin'}}
        with patch.object(security, 'decode_token', return_value=payload), patch.object(
            security, 'load_profile', AsyncMock(return_value={'id': payload['sub'], 'role': 'cliente'})
        ) as lookup:
            self.assertEqual(self.request('signed-token').status_code, 403)
            lookup.assert_awaited_once_with(payload['sub'])

    def test_invalid_token_and_jwks_outage(self):
        self.configure_supabase()
        for error, expected in [(jwt.ExpiredSignatureError('secret'), 401),
                                (jwt.PyJWKClientConnectionError('secret'), 503)]:
            with patch.object(security, 'decode_token', side_effect=error):
                response = self.request('invalid')
                self.assertEqual(response.status_code, expected)
                self.assertNotIn('secret', response.text)


class ProfileTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_invalid_and_unavailable_profiles(self):
        for data in ([], [{'id': 'other', 'role': 'admin'}], [{'id': 'user', 'role': 'owner'}]):
            response = Mock()
            response.json.return_value = data
            client = AsyncMock()
            client.get.return_value = response
            with patch.object(security.httpx, 'AsyncClient') as factory:
                factory.return_value.__aenter__.return_value = client
                with self.assertRaises(security.HTTPException) as caught:
                    await security.load_profile('user')
                self.assertEqual(caught.exception.status_code, 403)
        with patch.object(security.httpx, 'AsyncClient') as factory:
            factory.return_value.__aenter__.side_effect = httpx.ConnectError('private')
            with self.assertRaises(security.HTTPException) as caught:
                await security.load_profile('user')
            self.assertEqual(caught.exception.status_code, 503)


if __name__ == '__main__':
    unittest.main()

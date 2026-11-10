import unittest
from types import SimpleNamespace
from app.core.supabase_headers import service_headers
from app.core.operations import validate_production


class ProductionTests(unittest.TestCase):
    def test_secret_key_is_not_used_as_jwt(self):
        self.assertEqual(service_headers('sb_secret_example'), {'apikey': 'sb_secret_example'})
        self.assertEqual(service_headers('legacy'), {'apikey': 'legacy', 'Authorization': 'Bearer legacy'})

    def test_production_rejects_debug_demo_and_http_origins(self):
        values = dict(APP_ENV='production', DEBUG=False, ENABLE_DEMO_AUTH=False, RBAC_DATABASE_ENABLED=True,
                      SUPABASE_URL='https://example.supabase.co', SUPABASE_SERVICE_ROLE_KEY='test',
                      SUPABASE_JWKS_URL='https://example.supabase.co/keys', SUPABASE_JWT_ISSUER='https://example.supabase.co/auth/v1',
                      ALLOWED_ORIGINS=['https://example.host'])
        validate_production(SimpleNamespace(**values))
        for bad in [{'DEBUG': True}, {'ENABLE_DEMO_AUTH': True}, {'ALLOWED_ORIGINS': ['http://localhost:5173']}, {'RBAC_DATABASE_ENABLED': False}]:
            with self.assertRaises(RuntimeError): validate_production(SimpleNamespace(**{**values, **bad}))

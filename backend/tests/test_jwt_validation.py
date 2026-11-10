import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from app.core.security import decode_token
from app.core.config import Settings


class JwtValidationTests(unittest.TestCase):
    def setUp(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.settings = Settings(_env_file=None, DEBUG=True,
            SUPABASE_JWT_ISSUER='https://example.supabase.co/auth/v1',
            SUPABASE_JWKS_URL='https://example.supabase.co/auth/v1/.well-known/jwks.json')
        self.settings_patch = patch('app.core.security.settings', self.settings)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        client = SimpleNamespace(get_signing_key_from_jwt=lambda _: SimpleNamespace(key=self.key.public_key()))
        self.jwks_patch = patch('app.core.security.get_jwks_client', return_value=client)
        self.jwks_patch.start()
        self.addCleanup(self.jwks_patch.stop)

    def token(self, **claims):
        payload = {'sub': '00000000-0000-4000-8000-000000000001', 'aud': 'authenticated',
                   'iss': self.settings.SUPABASE_JWT_ISSUER, 'exp': int(time.time())+3600, 'iat': int(time.time())}
        payload.update(claims)
        return jwt.encode(payload, self.key, algorithm='ES256', headers={'kid': 'test-key'})

    def test_small_clock_difference_accepts_valid_signature(self):
        now = int(time.time())
        self.assertEqual(decode_token(self.token(iat=now+5, nbf=now+5))['aud'], 'authenticated')

    def test_large_clock_difference_is_rejected(self):
        with self.assertRaises(jwt.ImmatureSignatureError):
            decode_token(self.token(iat=int(time.time())+120))

    def test_expired_token_is_rejected(self):
        with self.assertRaises(jwt.ExpiredSignatureError):
            decode_token(self.token(exp=int(time.time())-120))

    def test_incorrect_issuer_audience_and_signature_are_rejected(self):
        for claims in [{'iss': 'https://other.supabase.co/auth/v1'}, {'aud': 'other'}]:
            with self.assertRaises(jwt.PyJWTError):
                decode_token(self.token(**claims))
        other_key = ec.generate_private_key(ec.SECP256R1())
        payload = jwt.decode(self.token(), options={'verify_signature': False})
        token = jwt.encode(payload, other_key, algorithm='ES256', headers={'kid': 'test-key'})
        with self.assertRaises(jwt.InvalidSignatureError):
            decode_token(token)

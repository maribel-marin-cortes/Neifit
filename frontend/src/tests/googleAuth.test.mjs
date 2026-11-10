import { test } from 'node:test';
import assert from 'node:assert/strict';
import { startGoogleSignIn, finishGoogleSignIn } from '../services/googleAuth.js';

test('inicia Google con callback del origen actual y sin permisos de Gmail', async () => {
  let options;
  const auth = { async signInWithOAuth(value) { options = value; return { data: { url: 'https://example.supabase.co/auth/v1/authorize' }, error: null }; } };
  await startGoogleSignIn(auth, 'http://127.0.0.1:5173');
  assert.deepEqual(options, {
    provider: 'google',
    options: { redirectTo: 'http://127.0.0.1:5173/auth/callback', queryParams: { prompt: 'select_account' }, skipBrowserRedirect: true },
  });
});

test('no simula acceso si falta configuración o falla el proveedor', async () => {
  await assert.rejects(startGoogleSignIn(null, 'http://localhost:5173'), /no está disponible/);
  await assert.rejects(startGoogleSignIn({ signInWithOAuth: async () => ({ error: new Error('Proveedor deshabilitado') }) }, 'http://localhost:5173'), /deshabilitado/);
});

test('rechaza callback sin sesión', async () => {
  await assert.rejects(finishGoogleSignIn({ auth: { getSession: async () => ({ data: { session: null }, error: null }) } }), /No se completó/);
});

test('el callback consulta el perfil del usuario y no acepta roles de metadatos', async () => {
  let selectedId;
  const client = {
    auth: { getSession: async () => ({ data: { session: { user: { id: 'google-user', user_metadata: { role: 'admin' } } } }, error: null }) },
    from(table) {
      assert.equal(table, 'profiles');
      return { select: () => ({ eq: (_, id) => {
        selectedId = id;
        return { single: async () => ({ data: { id: 'google-user', role: 'cliente' }, error: null }) };
      } }) };
    },
  };
  assert.equal((await finishGoogleSignIn(client)).role, 'cliente');
  assert.equal(selectedId, 'google-user');
  client.from = () => ({ select: () => ({ eq: () => ({ single: async () => ({ data: null, error: new Error('missing') }) }) }) });
  await assert.rejects(finishGoogleSignIn(client), /perfil/);
});

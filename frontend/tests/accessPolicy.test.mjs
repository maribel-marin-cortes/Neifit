import { test } from 'node:test';
import assert from 'node:assert/strict';
import { safeReturnTo, loginLink, loginDestination } from '../src/services/accessPolicy.js';
import { startGoogleSignIn } from '../src/services/googleAuth.js';

test('solo permite destinos internos seguros y evita bucles de autenticación', () => {
  for (const value of [null, 'https://example.com', '//example.com', '/\\example.com', '/login', '/registro', '/auth/callback', '/recuperar-contrasena']) {
    assert.equal(safeReturnTo(value), '/catalogo');
  }
  assert.equal(safeReturnTo('/productos/mousse-natural-de-mango?origen=inicio'), '/productos/mousse-natural-de-mango?origen=inicio');
});

test('conserva producto seleccionado y filtra destinos por rol', () => {
  assert.equal(loginLink('/productos/mango'), '/login?next=%2Fproductos%2Fmango');
  assert.equal(loginDestination('/productos/mango', 'cliente'), '/productos/mango');
  assert.equal(loginDestination('/admin', 'cliente'), '/catalogo');
  assert.equal(loginDestination('/admin', 'admin'), '/admin');
  assert.equal(loginDestination('/catalogo', 'mensajeria'), '/mensajeria');
});

test('Google conserva el destino de regreso mediante callback local', async () => {
  let request;
  await startGoogleSignIn({ signInWithOAuth: async value => {
    request = value;
    return { data: { url: 'https://example.supabase.co/auth/v1/authorize' }, error: null };
  } }, 'http://127.0.0.1:5173', '/productos/mango');
  const callback = new URL(request.options.redirectTo);
  assert.equal(callback.pathname, '/auth/callback');
  assert.equal(callback.searchParams.get('next'), '/productos/mango');
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createPasswordRecovery, hasRecoveryLinkError, isRecoveryCallback, readRecoveryTokenHash, RECOVERY_SENT_MESSAGE } from '../services/passwordRecovery.js';

function setup(options = {}) {
  let callback;
  let session = null;
  const saved = new Map();
  const calls = [];
  const auth = {
    onAuthStateChange(cb) { callback = cb; return { data: { subscription: { unsubscribe() {} } } }; },
    async getSession() { return { data: { session }, error: null }; },
    async resetPasswordForEmail(...args) { calls.push(['request', ...args]); return { error: null }; },
    async updateUser(data) { calls.push(['update', data]); return { error: null }; },
    async signOut(options) { calls.push(['signOut', options]); callback('SIGNED_OUT', null); return { error: null }; },
  };
  const service = createPasswordRecovery(auth, {
    origin: 'http://127.0.0.1:5173',
    ...options,
    storage: { getItem: k => saved.get(k), setItem: (k, v) => saved.set(k, v), removeItem: k => saved.delete(k) },
  });
  return { service, auth, calls, saved, event(name, id = 'user-1') {
    session = id ? { user: { id } } : null;
    callback(name, session);
  } };
}

test('solicita enlace al origen actual con ruta exacta y sin contraseña', async () => {
  const { service, calls } = setup();
  assert.equal(await service.request(' persona@example.com '), RECOVERY_SENT_MESSAGE);
  assert.deepEqual(calls, [['request', 'persona@example.com', { redirectTo: 'http://127.0.0.1:5173/restablecer-contrasena' }]]);
});

test('una sesión de login normal no habilita recuperación', async () => {
  const { service, event, calls } = setup();
  event('SIGNED_IN');
  assert.equal(await service.hasRecoverySession(), false);
  await assert.rejects(service.update('ClaveLarga123!', 'ClaveLarga123!'), /enlace/);
  assert.equal(calls.length, 0);
});

test('recuperación válida actualiza contraseña, limpia marcador y cierra sesión local', async () => {
  const { service, event, calls, saved } = setup();
  event('PASSWORD_RECOVERY');
  event('SIGNED_IN'); // Evento que también puede emitirse al recuperar foco.
  assert.equal(await service.hasRecoverySession(), true);
  await service.update('ClaveLarga123!', 'ClaveLarga123!');
  assert.deepEqual(calls, [['update', { password: 'ClaveLarga123!' }], ['signOut', { scope: 'local' }]]);
  assert.equal(saved.size, 0);
  assert.equal(await service.hasRecoverySession(), false);
});

test('rechaza contraseña corta y confirmación diferente sin llamar a Supabase', async () => {
  const { service, event, calls } = setup();
  event('PASSWORD_RECOVERY');
  await assert.rejects(service.update('corta', 'corta'), /8 caracteres/);
  await assert.rejects(service.update('ClaveLarga123!', 'Diferente123!'), /no coinciden/);
  assert.equal(calls.length, 0);
});

test('un usuario distinto o sin sesión invalida el enlace', async () => {
  const { service, event } = setup();
  event('PASSWORD_RECOVERY');
  event('SIGNED_IN', 'otro-usuario');
  assert.equal(await service.hasRecoverySession(), false);
  event('SIGNED_OUT', null);
  assert.equal(await service.hasRecoverySession(), false);
});

test('los errores de envío se propagan y nunca se simula envío exitoso', async () => {
  const { service, auth } = setup();
  auth.resetPasswordForEmail = async () => ({ error: { status: 429, message: 'Rate limit' } });
  await assert.rejects(service.request('persona@example.com'), e => e.status === 429);
  auth.resetPasswordForEmail = async () => ({ error: { code: 'user_not_found' } });
  assert.equal(await service.request('desconocido@example.com'), RECOVERY_SENT_MESSAGE);
});

test('si falla updateUser conserva el estado y no cierra sesión', async () => {
  const { service, auth, event, calls } = setup();
  event('PASSWORD_RECOVERY');
  auth.updateUser = async () => ({ error: new Error('Contraseña rechazada') });
  await assert.rejects(service.update('ClaveLarga123!', 'ClaveLarga123!'), /rechazada/);
  assert.equal(await service.hasRecoverySession(), true);
  assert.equal(calls.length, 0);
});

test('detecta enlace caducado en hash o query, sin tratar parámetros normales como error', () => {
  assert.equal(hasRecoveryLinkError('http://localhost:5173/restablecer-contrasena#error_code=otp_expired'), true);
  assert.equal(hasRecoveryLinkError('http://localhost:5173/restablecer-contrasena?error=access_denied'), true);
  assert.equal(hasRecoveryLinkError('http://localhost:5173/restablecer-contrasena#type=recovery'), false);
});

test('espera PASSWORD_RECOVERY cuando getSession se resuelve antes que el evento real del SDK', async () => {
  const { service, auth, event } = setup({ callbackExpected: true });
  auth.getSession = async () => ({ data: { session: { user: { id: 'user-1' } } }, error: null });
  const checks = [service.hasRecoverySession(), service.hasRecoverySession()];
  setTimeout(() => event('PASSWORD_RECOVERY'), 10);
  assert.deepEqual(await Promise.all(checks), [true, true]);
});

test('la URL de recuperación por sí sola no habilita una sesión normal', async () => {
  const { service, auth } = setup({ callbackExpected: true, eventTimeoutMs: 5 });
  auth.getSession = async () => ({ data: { session: { user: { id: 'user-1' } } }, error: null });
  assert.equal(await service.hasRecoverySession(), false);
});

test('reconoce callbacks antes de que Supabase limpie la URL y descarta errores', () => {
  assert.equal(isRecoveryCallback('http://localhost:5173/restablecer-contrasena#type=recovery&access_token=test'), true);
  assert.equal(isRecoveryCallback('http://localhost:5173/restablecer-contrasena?code=test'), true);
  assert.equal(isRecoveryCallback('http://localhost:5173/restablecer-contrasena#error=access_denied&type=recovery'), false);
  assert.equal(isRecoveryCallback('http://localhost:5173/restablecer-contrasena'), false);
  assert.equal(isRecoveryCallback('http://localhost:5173/login#type=recovery'), false);
});

test('el enlace personalizado no se verifica hasta que el usuario pulsa continuar', async () => {
  let cleaned = 0;
  const { service, auth, event, calls } = setup({ tokenHash: 'test-hash', clearRecoveryUrl: () => { cleaned++; } });
  auth.verifyOtp = async data => {
    calls.push(['verify', data]);
    event('SIGNED_IN');
    return { data: { session: { user: { id: 'user-1' } } }, error: null };
  };
  assert.equal(service.hasPendingLink(), true);
  assert.equal(await service.hasRecoverySession(), false);
  assert.equal(calls.length, 0);
  await Promise.all([service.confirmLink(), service.confirmLink()]);
  assert.deepEqual(calls, [['verify', { token_hash: 'test-hash', type: 'recovery' }]]);
  assert.equal(service.hasPendingLink(), false);
  assert.equal(await service.hasRecoverySession(), true);
  assert.equal(cleaned, 1);
});

test('rechaza OTP caducado y no habilita actualización de contraseña', async () => {
  const { service, auth } = setup({ tokenHash: 'expired-hash' });
  auth.verifyOtp = async () => ({ data: null, error: { code: 'otp_expired' } });
  await assert.rejects(service.confirmLink(), error => error.code === 'otp_expired');
  assert.equal(await service.hasRecoverySession(), false);
});

test('un límite temporal permite reintentar la verificación sin perder el enlace', async () => {
  const { service, auth, event } = setup({ tokenHash: 'test-hash' });
  auth.verifyOtp = async () => ({ data: null, error: { status: 429 } });
  await assert.rejects(service.confirmLink(), error => error.status === 429);
  assert.equal(service.hasPendingLink(), true);
  auth.verifyOtp = async () => {
    event('PASSWORD_RECOVERY');
    return { data: { session: { user: { id: 'user-1' } } }, error: null };
  };
  await service.confirmLink();
  assert.equal(await service.hasRecoverySession(), true);
});

test('solo acepta hashes con ruta y tipo de recuperación correctos', () => {
  assert.equal(readRecoveryTokenHash('https://example.com/restablecer-contrasena?token_hash=test&type=recovery'), 'test');
  for (const path of ['/login?token_hash=test&type=recovery', '/restablecer-contrasena?token_hash=test&type=signup', '/restablecer-contrasena?type=recovery']) {
    assert.equal(readRecoveryTokenHash('https://example.com' + path), null);
  }
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

test('el catálogo envía filtros booleanos y la consulta administrativa incluye inactivos', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: true, json: async () => [] }));
  await api.getProducts({ available: true, include_inactive: true, featured: false });
  const url = new URL(requests[0][0]);
  assert.equal(url.searchParams.get('available'), 'true');
  assert.equal(url.searchParams.get('include_inactive'), 'true');
  assert.equal(url.searchParams.get('featured'), 'false');
});

test('las acciones administrativas usan la API y conservan la sesión del administrador', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: true, json: async () => ({ id: 'saved' }) }));
  await api.assignDelivery('order-test', 'courier-test');
  await api.updateQuoteStatus('quote-test', 'respondida');
  assert.equal(requests[0][1].method, 'PATCH');
  assert.equal(JSON.parse(requests[0][1].body).user_id, 'courier-test');
  assert.equal(requests[1][1].headers.Authorization, 'Bearer supabase-jwt');
  assert.equal(JSON.parse(requests[1][1].body).status, 'respondida');
});

test('mensajería usa las rutas reales publicadas por el backend', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: true, json: async () => [] }));
  await api.getDeliveryRequests();
  await api.approveDeliveryRequest('11111111-1111-4111-8111-111111111111');
  assert.equal(new URL(requests[0][0]).pathname, '/api/v1/solicitudes-mensajeria');
  assert.equal(new URL(requests[1][0]).pathname,
    '/api/v1/solicitudes-mensajeria/11111111-1111-4111-8111-111111111111/aprobar');
});

async function loadApi(configured, fetchImpl, session = { access_token: 'supabase-jwt' }, refresh = async () => ({ data: { session: { access_token: 'renewed-jwt' } }, error: null })) {
  const storage = new Map([['neifit_token', 'old-demo-token']]);
  const requests = [];
  const context = vm.createContext({
    URLSearchParams,
    console: { warn() {}, error() {} },
    localStorage: { getItem: key => storage.get(key) ?? null, setItem: (k, v) => storage.set(k, v) },
    fetch: async (...args) => { requests.push(args); return fetchImpl(...args); },
  });
  const fixtures = new vm.SyntheticModule([
    'initialCategories', 'initialProducts', 'initialOrders', 'initialQuotes',
    'initialCompanySettings', 'initialSiteContent', 'initialCompanyValues',
  ], function () {
    for (const key of ['initialCategories', 'initialProducts', 'initialOrders', 'initialQuotes',
      'initialCompanySettings', 'initialSiteContent', 'initialCompanyValues']) {
      this.setExport(key, key === 'initialOrders' ? [{ id: 'demo-order' }] : []);
    }
  }, { context });
  const auth = new vm.SyntheticModule(['supabase', 'isSupabaseConfigured'], function () {
    this.setExport('isSupabaseConfigured', configured);
    this.setExport('supabase', { auth: {
      getSession: async () => ({ data: { session }, error: null }),
      refreshSession: async () => { const result = await refresh(); if (result.data?.session) session = result.data.session; return result; },
    } });
  }, { context });
  const source = await readFile(new URL('../services/api.js', import.meta.url), 'utf8');
  const module = new vm.SourceTextModule(source, {
    context, initializeImportMeta(meta) { meta.env = {}; },
  });
  await module.link(specifier => {
    if (specifier === './mockData') return fixtures;
    if (specifier === './supabaseClient') return auth;
    throw new Error(`Import inesperado: ${specifier}`);
  });
  await module.evaluate();
  return { api: module.namespace.api, requests, storage };
}

test('la API usa el JWT de sesión real y descarta el token demo guardado', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: true, json: async () => [] }));
  await api.getOrders();
  assert.equal(requests[0][1].headers.Authorization, 'Bearer supabase-jwt');
});

test('un 403 real se propaga y no crea un pedido local', async () => {
  const { api, storage } = await loadApi(true, async () => ({
    ok: false, status: 403, json: async () => ({ detail: 'Acceso denegado' }),
  }));
  await assert.rejects(api.createOrder({ items: [] }), /Acceso denegado/);
  assert.equal(storage.has('neifit_orders'), false);
});

test('sin conexión, el modo Supabase no devuelve pedidos demo', async () => {
  const { api } = await loadApi(true, async () => { throw new Error('Sin conexión'); });
  await assert.rejects(api.getOrders(), /Sin conexión/);
});

test('sin sesión real no se envía el token demo anterior', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: true, json: async () => [] }), null);
  await api.getOrders();
  assert.equal(requests[0][1].headers.Authorization, undefined);
});

test('el respaldo local sigue funcionando sin Supabase configurado', async () => {
  const { api } = await loadApi(false, async () => { throw new Error('Sin conexión'); });
  const orders = await api.getOrders();
  assert.equal(orders[0].id, 'demo-order');
});

test('un token rechazado se renueva una vez y el reintento usa el nuevo JWT', async () => {
  let refreshes = 0;
  const { api, requests } = await loadApi(true, async (_, options) => options.headers.Authorization === 'Bearer renewed-jwt'
    ? { ok: true, status: 200, json: async () => ({ id: 'user' }) }
    : { ok: false, status: 401, json: async () => ({ detail: 'Expired' }) }, undefined,
  async () => { refreshes++; return { data: { session: { access_token: 'renewed-jwt' } }, error: null }; });
  assert.equal((await api.getCurrentUser()).id, 'user');
  assert.equal(refreshes, 1);
  assert.equal(requests.length, 2);
});

test('un segundo 401 se propaga sin bucle ni éxito simulado', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: false, status: 401, json: async () => ({ detail: 'Sesión inválida' }) }));
  await assert.rejects(api.getCurrentUser(), error => error.status === 401);
  assert.equal(requests.length, 2);
});

test('una renovación fallida no reintenta la operación', async () => {
  const { api, requests } = await loadApi(true, async () => ({ ok: false, status: 401 }), undefined,
    async () => ({ data: { session: null }, error: new Error('Sesión caducada') }));
  await assert.rejects(api.getCurrentUser(), /caducada/);
  assert.equal(requests.length, 1);
});

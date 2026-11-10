import { test } from 'node:test';
import assert from 'node:assert/strict';
import { requiredRoutePermission } from '../src/services/routePermissions.js';

test('módulos requieren permisos específicos', () => {
  assert.equal(requiredRoutePermission('/catalogo'), 'catalog.read');
  assert.equal(requiredRoutePermission('/carrito'), 'orders.create');
  assert.equal(requiredRoutePermission('/cotizador'), 'quotes.create');
  assert.equal(requiredRoutePermission('/mensajeria'), 'delivery.read_assigned');
  assert.equal(requiredRoutePermission('/admin', '?modulo=accesos'), 'access.manage');
  assert.equal(requiredRoutePermission('/admin', '?modulo=productos'), 'products.manage');
  assert.equal(requiredRoutePermission('/'), null);
});

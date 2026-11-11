import test from 'node:test';
import assert from 'node:assert/strict';
import { adminOrderStatusOptions, nextOrderStatus, orderStatusLabel } from '../services/orderStatusFlow.js';

test('usa el flujo corto de cuatro estados', () => {
  assert.equal(nextOrderStatus('recibido'), 'en_preparacion');
  assert.equal(nextOrderStatus('en_preparacion'), 'en_ruta');
  assert.equal(nextOrderStatus('en_ruta'), 'entregado');
  assert.equal(nextOrderStatus('entregado'), null);
});

test('permite continuar pedidos que conservan estados anteriores', () => {
  assert.equal(nextOrderStatus('confirmado'), 'en_preparacion');
  assert.equal(nextOrderStatus('empacado'), 'en_ruta');
  assert.equal(nextOrderStatus('despachado'), 'en_ruta');
});

test('el administrador solo recibe la siguiente acción y excepciones', () => {
  assert.deepEqual(adminOrderStatusOptions('recibido'), ['recibido', 'en_preparacion', 'novedad', 'cancelado']);
  assert.deepEqual(adminOrderStatusOptions('entregado'), ['entregado']);
  assert.equal(orderStatusLabel('en_preparacion'), 'En preparación');
});

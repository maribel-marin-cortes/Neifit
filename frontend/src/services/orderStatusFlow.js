export const ORDER_STATUS_LABELS = {
  recibido: 'Recibido',
  en_preparacion: 'En preparación',
  en_ruta: 'En ruta',
  entregado: 'Entregado',
  novedad: 'Novedad',
  cancelado: 'Cancelado',
};

// Los estados anteriores siguen avanzando para no bloquear pedidos históricos.
const NEXT_STATUS = {
  recibido: 'en_preparacion',
  confirmado: 'en_preparacion',
  en_preparacion: 'en_ruta',
  empacado: 'en_ruta',
  despachado: 'en_ruta',
  en_ruta: 'entregado',
};

export function nextOrderStatus(current) {
  return NEXT_STATUS[current] || null;
}

export function adminOrderStatusOptions(current) {
  if (['entregado', 'cancelado'].includes(current)) return [current];
  const next = nextOrderStatus(current);
  return [...new Set([current, next, 'novedad', 'cancelado'].filter(Boolean))];
}

export function orderStatusLabel(status) {
  return ORDER_STATUS_LABELS[status] || status.replace(/_/g, ' ');
}

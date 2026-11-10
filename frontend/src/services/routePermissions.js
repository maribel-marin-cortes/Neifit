export function requiredRoutePermission(pathname, search = '') {
  if (pathname.startsWith('/admin')) {
    const module = new URLSearchParams(search).get('modulo');
    return ({ accesos: 'access.manage', productos: 'products.manage', cotizaciones: 'quotes.manage' })[module] || 'orders.manage';
  }
  if (pathname.startsWith('/mensajeria')) return 'delivery.read_assigned';
  if (pathname.startsWith('/catalogo') || pathname.startsWith('/productos')) return 'catalog.read';
  if (pathname === '/carrito' || pathname === '/checkout') return 'orders.create';
  if (pathname === '/cotizador') return 'quotes.create';
  if (pathname === '/mis-pedidos' || pathname.startsWith('/seguimiento')) return 'orders.read_own';
  if (pathname === '/mi-cuenta') return 'profile.read';
  return null;
}

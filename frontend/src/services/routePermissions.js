export function requiredRoutePermission(pathname, search = '') {
  if (pathname === '/usuarios') return 'users.manage';
  if (pathname.startsWith('/admin')) {
    if (pathname.startsWith('/admin/productos/')) return 'products.manage';
    const module = new URLSearchParams(search).get('modulo');
    return ({ accesos: 'access.manage', productos: 'products.manage', cotizaciones: 'quotes.manage', contenido: 'content.manage' })[module] || 'orders.manage';
  }
  if (pathname.startsWith('/mensajeria')) return 'delivery.read_assigned';
  if (pathname.startsWith('/catalogo') || pathname.startsWith('/productos')) return 'catalog.read';
  if (pathname === '/carrito' || pathname === '/checkout') return 'orders.create';
  if (pathname === '/cotizador') return 'quotes.create';
  if (pathname === '/mis-cotizaciones') return 'quotes.read_own';
  if (pathname === '/mis-pedidos' || pathname.startsWith('/seguimiento')) return 'orders.read_own';
  if (pathname === '/mi-cuenta') return 'profile.read';
  return null;
}

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, LayoutGrid, CakeSlice, Nut, CupSoda, ShoppingBag, FileText, MapPin, User, ClipboardList, LayoutDashboard, Package, Truck, LogIn } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { requiredRoutePermission } from '../services/routePermissions';

export default function Sidebar({ open }) {
  const { user, isMensajeria, hasPermission } = useAuth();
  const { totalItemsCount } = useCart();
  const { pathname, search } = useLocation();
  const params = new URLSearchParams(search);
  const groups = [
    { title: 'Explorar', items: [
      { to: '/', label: 'Inicio', icon: Home },
      { to: '/catalogo', label: 'Catálogo', icon: LayoutGrid },
      { to: '/catalogo?cat=postres', label: 'Postres', icon: CakeSlice },
      { to: '/catalogo?cat=snacks', label: 'Snacks', icon: Nut },
      { to: '/catalogo?cat=bebidas', label: 'Bebidas', icon: CupSoda },
    ] },
    { title: 'Compras y pedidos', items: [
      { to: '/carrito', label: 'Carrito de compras', icon: ShoppingBag, count: totalItemsCount },
      { to: '/cotizador', label: 'Cotizador', icon: FileText },
      { to: '/mis-cotizaciones', label: 'Mis cotizaciones', icon: FileText },
      { to: '/seguimiento', label: 'Seguimiento de pedido', icon: MapPin },
      ...(user && !isMensajeria ? [{ to: '/mis-pedidos', label: 'Mis pedidos', icon: ClipboardList }] : []),
    ] },
    { title: 'Mi cuenta', items: user
      ? [{ to: '/mi-cuenta', label: 'Mi perfil', icon: User }]
      : [{ to: '/login', label: 'Iniciar sesión', icon: LogIn }] },
  ];
  groups.push({ title: 'Administración', items: [
    { to: '/admin', label: 'Resumen', icon: LayoutDashboard },
    { to: '/admin?modulo=productos', label: 'Productos e inventario', icon: Package },
    { to: '/admin?modulo=pedidos', label: 'Pedidos', icon: ShoppingBag },
    { to: '/admin?modulo=cotizaciones', label: 'Cotizaciones', icon: FileText },
    { to: '/admin?modulo=contenido', label: 'Contenido institucional', icon: FileText },
    { to: '/admin?modulo=accesos', label: 'Roles y permisos', icon: User },
    { to: '/usuarios', label: 'Usuarios', icon: User },
  ] });
  groups.push({ title: 'Entregas', items: [
    { to: '/mensajeria', label: 'Mensajería', icon: Truck },
  ] });
  const roleGroups = isMensajeria
    ? [{ title: 'Principal', items: [{ to: '/', label: 'Inicio', icon: Home }] }, ...groups.filter(group => ['Mi cuenta', 'Entregas'].includes(group.title))]
    : groups;
  const visibleGroups = roleGroups.map(group => ({
    ...group,
    items: group.items.filter(item => {
      const url = new URL(item.to, 'https://neifit.invalid');
      const permission = requiredRoutePermission(url.pathname, url.search);
      return !permission || hasPermission(permission);
    }),
  })).filter(group => group.items.length > 0);

  function isActive(to) {
    const target = new URL(to, 'https://neifit.invalid');
    if (target.pathname === '/catalogo') return pathname === '/catalogo' && (target.searchParams.get('cat') || '') === (params.get('cat') || '');
    if (target.pathname === '/admin') return pathname.startsWith('/admin') && (target.searchParams.get('modulo') || 'dashboard') === (params.get('modulo') || 'dashboard');
    if (target.pathname === '/seguimiento') return pathname.startsWith('/seguimiento');
    return pathname === target.pathname;
  }

  return (
    <aside id="menu-modulos" aria-label="Menú de módulos" className={`${open ? 'block' : 'hidden'} bg-[#FFF8F2] border-b lg:border-b-0 lg:border-r border-[#7A4E2D]/15`}>
      <div className="p-4 sm:p-5 lg:sticky lg:top-20 lg:max-h-[calc(100dvh-5rem)] lg:overflow-y-auto">
        <nav aria-label="Módulos de Neifit" className="space-y-6">
          {visibleGroups.map(group => <div key={group.title}>
            <p className="text-[11px] font-bold uppercase tracking-wider text-[#7A4E2D] mb-2 px-3">{group.title}</p>
            <ul className="space-y-1">
              {group.items.map(({ to, label, icon: Icon, count }) => {
                const active = isActive(to);
                return <li key={to}>
                  <Link to={to} aria-current={active ? 'page' : undefined}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#7A4E2D] ${active ? 'bg-[#7A4E2D] text-white' : 'text-[#4B2E1F] hover:bg-[#F6E7D8]'}`}>
                    <Icon aria-hidden="true" className="w-[18px] h-[18px] shrink-0" />
                    <span className="flex-1">{label}</span>
                    {count > 0 && <span className="rounded-full bg-[#F6E7D8] text-[#4B2E1F] px-2 text-xs">{count}</span>}
                  </Link>
                </li>;
              })}
            </ul>
          </div>)}
        </nav>
      </div>
    </aside>
  );
}

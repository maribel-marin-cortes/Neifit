import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingBag, Menu, X, User, MessageCircle, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import Notifications from './Notifications';
import { useCompanyTheme } from '../context/ThemeContext';

export default function Navbar({ menuOpen = false, onToggleMenu, showModules = true }) {
  const { user, logout, hasPermission } = useAuth();
  const { totalItemsCount } = useCart();
  const { theme } = useCompanyTheme();
  const [error, setError] = useState('');
  const navigate = useNavigate();
  async function handleLogout() {
    try { await logout(); navigate('/'); } catch { setError('No se pudo cerrar la sesión. Inténtalo de nuevo.'); }
  }
  return (
    <header className="sticky top-0 z-40 bg-[#F6E7D8]/95 backdrop-blur-md border-b border-[#7A4E2D]/15 shadow-sm">
      <div className="h-20 px-4 sm:px-6 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          {showModules && <button type="button" onClick={onToggleMenu} aria-expanded={menuOpen} aria-controls="menu-modulos"
            aria-label={menuOpen ? 'Cerrar menú de módulos' : 'Abrir menú de módulos'}
            className="p-2 rounded-xl text-[#7A4E2D] hover:bg-[#FFF8F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#7A4E2D]">
            {menuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>}
          <Link to="/" aria-label="Neifit, ir al inicio" className="shrink-0">
            <img src={theme.logo_url || '/logo-neifit-tropical.png'} alt="Logo de la empresa" className="h-16 w-24 object-contain" />
          </Link>
          <p className="hidden sm:block text-xs text-[#7A4E2D] border-l border-[#7A4E2D]/20 pl-4">Postres, snacks y bebidas<br /><span className="font-semibold text-[#4B2E1F]">Sabores de nuestras raíces</span></p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {user && <Notifications key={user.id} />}
          <a href="https://wa.me/573127827020" target="_blank" rel="noopener noreferrer" className="hidden md:inline-flex items-center gap-2 rounded-full bg-[#5F8D4E] text-white text-xs font-semibold px-4 py-2" aria-label="Contactar por WhatsApp a Neifit">
            <MessageCircle className="h-4 w-4" /> WhatsApp
          </a>
          {user && hasPermission('orders.create') && <Link to="/carrito" aria-label={`Ver carrito de compras con ${totalItemsCount} productos`} className="relative p-2.5 rounded-xl bg-[#FFF8F2] text-[#7A4E2D] border border-[#7A4E2D]/20">
            <ShoppingBag className="h-5 w-5" />
            {totalItemsCount > 0 && <span className="absolute -top-1 -right-1 rounded-full bg-[#7A4E2D] text-white text-[10px] px-1.5">{totalItemsCount}</span>}
          </Link>}
          {user ? <details className="relative">
            <summary className="cursor-pointer flex items-center gap-2 text-xs font-semibold bg-[#FFF8F2] text-[#4B2E1F] border border-[#7A4E2D]/20 rounded-xl px-3 py-2.5">
              <User className="h-4 w-4" /><span className="hidden sm:inline max-w-28 truncate">{user.full_name?.split(' ')[0] || 'Mi cuenta'}</span><span className="sm:hidden">Cuenta</span>
            </summary>
            <div className="absolute right-0 top-full mt-2 w-56 rounded-xl bg-[#FFF8F2] shadow-lg border border-[#7A4E2D]/15 p-2">
              <p className="px-3 py-2 text-xs text-[#7A4E2D] truncate">{user.email}</p>
              <Link to="/mi-cuenta" className="block px-3 py-2 rounded-lg text-sm hover:bg-[#F6E7D8]">Mi perfil</Link>
              <button onClick={handleLogout} className="w-full flex gap-2 items-center px-3 py-2 rounded-lg text-sm text-red-700 hover:bg-red-50"><LogOut className="h-4 w-4" /> Cerrar sesión</button>
              {error && <p role="alert" className="text-xs text-red-700 p-2">{error}</p>}
            </div>
          </details> : <><Link to="/login" className="text-xs font-semibold text-[#7A4E2D] bg-[#FFF8F2] border border-[#7A4E2D]/20 px-3 py-2.5 rounded-xl">Ingresar</Link><Link to="/registro" className="text-xs font-semibold text-white bg-[#7A4E2D] px-3 py-2.5 rounded-xl">Crear cuenta</Link></>}
        </div>
      </div>
    </header>
  );
}

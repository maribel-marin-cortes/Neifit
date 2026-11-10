import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Footer from './Footer';
import WhatsAppButton from './WhatsAppButton';
import { useAuth } from '../context/AuthContext';

export default function SiteLayout({ children }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();
  useEffect(() => { setMenuOpen(false); }, [location.pathname, location.search]);
  useEffect(() => {
    const close = event => { if (event.key === 'Escape') setMenuOpen(false); };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, []);
  return (
    <div className="min-h-screen flex flex-col">
      <a href="#contenido-principal" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:bg-white focus:p-3 focus:rounded-lg">Saltar al contenido</a>
      <Navbar showModules={Boolean(user)} menuOpen={menuOpen} onToggleMenu={() => setMenuOpen(open => !open)} />
      <div className={`grid flex-1 ${user && menuOpen ? 'lg:grid-cols-[15rem_minmax(0,1fr)]' : 'grid-cols-1'}`}>
        {user && <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />}
        <main id="contenido-principal" tabIndex={-1} className="min-w-0 outline-none">{children}</main>
      </div>
      <Footer />
      <WhatsAppButton />
    </div>
  );
}

import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { loginLink } from '../services/accessPolicy';
import { requiredRoutePermission } from '../services/routePermissions';
import SiteLayout from '../components/SiteLayout';
import LandingPage from '../pages/LandingPage';
import CatalogoPage from '../pages/CatalogoPage';
import ProductoDetallePage from '../pages/ProductoDetallePage';
import CarritoPage from '../pages/CarritoPage';
import CheckoutPage from '../pages/CheckoutPage';
import LoginPage from '../pages/LoginPage';
import PasswordRecoveryPage from '../pages/PasswordRecoveryPage';
import GoogleCallbackPage from '../pages/GoogleCallbackPage';
import SeguimientoPage from '../pages/SeguimientoPage';
import CotizadorPage from '../pages/CotizadorPage';
import MisPedidosPage from '../pages/MisPedidosPage';
import MiCuentaPage from '../pages/MiCuentaPage';
import MisCotizacionesPage from '../pages/MisCotizacionesPage';
import AdminPage from '../pages/admin/AdminPage';
import AccessManagement from '../pages/admin/AccessManagement';
import ProductEditor from '../pages/admin/ProductEditor';
import MensajeriaPage from '../pages/mensajeria/MensajeriaPage';
import EmpresasPage from '../pages/EmpresasPage';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children, requiredRoles }) {
  const { user, loading, hasPermission } = useAuth();
  const location = useLocation();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 rounded-full border-4 border-[#7A4E2D] border-t-transparent" /></div>;
  if (!user) return <Navigate to={loginLink(location.pathname + location.search)} replace />;
  const permission = requiredRoutePermission(location.pathname, location.search);
  if (permission && !hasPermission(permission)) return <main className="min-h-screen flex flex-col gap-4 items-center justify-center px-4"><h1 className="text-2xl font-bold">Acceso no autorizado</h1><p>Tu rol no tiene permiso para este módulo.</p><a href="/" className="btn-primary">Volver al inicio</a></main>;
  if (requiredRoles && !requiredRoles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function LayoutWithNavFooter({ children }) {
  const { pathname } = useLocation();
  if (['/', '/politica-privacidad', '/terminos'].includes(pathname) || /^\/tienda\/[a-z0-9-]+$/.test(pathname)) return <SiteLayout>{children}</SiteLayout>;
  return <ProtectedRoute><SiteLayout>{children}</SiteLayout></ProtectedRoute>;
}

function LayoutMinimal({ children }) {
  return <main>{children}</main>;
}

export default function AppRouter() {
  return (
    <Routes>
      {/* Public routes with full layout */}
      <Route path="/" element={<LayoutWithNavFooter><LandingPage /></LayoutWithNavFooter>} />
      <Route path="/tienda/:empresa" element={<LayoutWithNavFooter><LandingPage /></LayoutWithNavFooter>} />
      <Route path="/tienda/:empresa/catalogo" element={<LayoutWithNavFooter><CatalogoPage /></LayoutWithNavFooter>} />
      <Route path="/tienda/:empresa/productos/:slug" element={<LayoutWithNavFooter><ProductoDetallePage /></LayoutWithNavFooter>} />
      <Route path="/catalogo" element={<LayoutWithNavFooter><CatalogoPage /></LayoutWithNavFooter>} />
      <Route path="/productos/:slug" element={<LayoutWithNavFooter><ProductoDetallePage /></LayoutWithNavFooter>} />
      <Route path="/carrito" element={<LayoutWithNavFooter><CarritoPage /></LayoutWithNavFooter>} />
      <Route path="/cotizador" element={<LayoutWithNavFooter><CotizadorPage /></LayoutWithNavFooter>} />
      <Route path="/seguimiento" element={<LayoutWithNavFooter><SeguimientoPage /></LayoutWithNavFooter>} />
      <Route path="/seguimiento/:codigo" element={<LayoutWithNavFooter><SeguimientoPage /></LayoutWithNavFooter>} />

      {/* Auth */}
      <Route path="/login" element={<LayoutMinimal><LoginPage /></LayoutMinimal>} />
      <Route path="/registro" element={<LayoutMinimal><LoginPage key="register" initialMode="register" /></LayoutMinimal>} />
      <Route path="/auth/callback" element={<LayoutMinimal><GoogleCallbackPage /></LayoutMinimal>} />
      <Route path="/recuperar-contrasena" element={<LayoutMinimal><PasswordRecoveryPage /></LayoutMinimal>} />
      <Route path="/restablecer-contrasena" element={<LayoutMinimal><PasswordRecoveryPage reset /></LayoutMinimal>} />

      {/* Authenticated routes */}
      <Route path="/mis-cotizaciones" element={<LayoutWithNavFooter><MisCotizacionesPage /></LayoutWithNavFooter>} />
      <Route path="/usuarios" element={<ProtectedRoute requiredRoles={['admin']}><SiteLayout><div className="max-w-7xl mx-auto p-6"><AccessManagement view="users" /></div></SiteLayout></ProtectedRoute>} />
      <Route path="/checkout" element={
        <LayoutWithNavFooter>
          <ProtectedRoute>
            <CheckoutPage />
          </ProtectedRoute>
        </LayoutWithNavFooter>
      } />
      <Route path="/mis-pedidos" element={
        <LayoutWithNavFooter>
          <ProtectedRoute>
            <MisPedidosPage />
          </ProtectedRoute>
        </LayoutWithNavFooter>
      } />
      <Route path="/mi-cuenta" element={
        <LayoutWithNavFooter>
          <ProtectedRoute>
            <MiCuentaPage />
          </ProtectedRoute>
        </LayoutWithNavFooter>
      } />
      <Route path="/empresas" element={<ProtectedRoute><SiteLayout><EmpresasPage /></SiteLayout></ProtectedRoute>} />

      {/* Admin panel */}
      <Route path="/admin/productos/nuevo" element={<ProtectedRoute><SiteLayout><ProductEditor /></SiteLayout></ProtectedRoute>} />
      <Route path="/admin/productos/:id/editar" element={<ProtectedRoute><SiteLayout><ProductEditor /></SiteLayout></ProtectedRoute>} />
      <Route path="/admin" element={
        <ProtectedRoute>
          <SiteLayout><AdminPage /></SiteLayout>
        </ProtectedRoute>
      } />
      <Route path="/admin/*" element={
        <ProtectedRoute>
          <SiteLayout><AdminPage /></SiteLayout>
        </ProtectedRoute>
      } />

      {/* Mensajería panel */}
      <Route path="/mensajeria" element={
        <ProtectedRoute>
          <SiteLayout><MensajeriaPage /></SiteLayout>
        </ProtectedRoute>
      } />

      {/* Legal pages */}
      <Route path="/politica-privacidad" element={
        <LayoutWithNavFooter>
          <div className="min-h-screen py-16 px-4 max-w-3xl mx-auto">
            <h1 className="font-display font-bold text-3xl text-[#4B2E1F] mb-6">Política de Privacidad</h1>
            <p className="text-[#7A4E2D]/80 leading-relaxed">
              En Neifit respetamos tu privacidad. Los datos que nos proporcionas (nombre, teléfono, dirección) se usan
              exclusivamente para gestionar tu pedido o cotización. No compartimos tu información con terceros sin tu
              consentimiento, salvo cuando sea requerido para el servicio de mensajería. Para consultas escríbenos a
              través de WhatsApp: +57 312 7827020.
            </p>
            <p className="text-sm text-[#7A4E2D]/50 mt-6">Medellín, Antioquia, Colombia.</p>
          </div>
        </LayoutWithNavFooter>
      } />
      <Route path="/terminos" element={
        <LayoutWithNavFooter>
          <div className="min-h-screen py-16 px-4 max-w-3xl mx-auto">
            <h1 className="font-display font-bold text-3xl text-[#4B2E1F] mb-6">Términos y Condiciones</h1>
            <p className="text-[#7A4E2D]/80 leading-relaxed">
              Al realizar un pedido en Neifit aceptas que los precios y disponibilidad están sujetos a confirmación.
              El domicilio aplica en Medellín. Los pedidos se procesan en el horario de atención: lunes a viernes,
              9:00 a. m. a 6:00 p. m. Las descripciones de productos Fuxion están basadas en información oficial
              del fabricante y no constituyen afirmaciones médicas.
            </p>
            <p className="text-sm text-[#7A4E2D]/50 mt-6">Medellín, Antioquia, Colombia.</p>
          </div>
        </LayoutWithNavFooter>
      } />

      {/* 404 */}
      <Route path="*" element={
        <LayoutWithNavFooter>
          <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center py-20">
            <p className="text-6xl">🍃</p>
            <h2 className="font-display font-bold text-3xl text-[#4B2E1F]">Página no encontrada</h2>
            <p className="text-[#7A4E2D]/70">La ruta que buscas no existe en Neifit.</p>
            <a href="/" className="btn-primary px-8">Volver al inicio</a>
          </div>
        </LayoutWithNavFooter>
      } />
    </Routes>
  );
}


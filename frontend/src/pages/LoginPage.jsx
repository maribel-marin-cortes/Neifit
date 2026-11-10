import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { safeReturnTo, loginDestination } from '../services/accessPolicy';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '../services/supabaseClient';
import { startGoogleSignIn, finishGoogleSignIn } from '../services/googleAuth';

export default function LoginPage({ initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode);
  const [searchParams] = useSearchParams();
  const next = safeReturnTo(searchParams.get('next'));
  const [form, setForm] = useState({ email: '', password: '', full_name: '', phone: '' });
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const { login, register, loginWithDemoRole } = useAuth();
  const navigate = useNavigate();

  const handleChange = e => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      if (mode === 'login') {
        const result = await login(form.email, form.password);
        const role = isSupabaseConfigured ? (await finishGoogleSignIn(supabase)).role : result.role;
        navigate(loginDestination(next, role), { replace: true });
        return;
      } else {
        const result = await register(form.email, form.password, form.full_name, form.phone);
        if (isSupabaseConfigured && !result.session) {
          setNotice('Revisa tu correo y confirma tu cuenta antes de iniciar sesión.');
          setMode('login');
          return;
        }
      }
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message || 'Error al autenticar. Verifica tus datos.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = (role) => {
    loginWithDemoRole(role);
    navigate(role === 'admin' ? '/admin' : role === 'mensajeria' ? '/mensajeria' : '/');
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setNotice(null);
    setGoogleLoading(true);
    try {
      const url = await startGoogleSignIn(supabase?.auth, window.location.origin, next);
      window.location.assign(url);
    } catch {
      setError('No se pudo iniciar el acceso con Google. Inténtalo de nuevo o utiliza tu correo y contraseña.');
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16 bg-[#F6E7D8]">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/">
            <img src="/logo-neifit-tropical.png" alt="Neifit" className="h-28 w-auto mx-auto mb-4 rounded-xl" />
          </Link>
          <h1 className="font-display font-bold text-2xl text-[#4B2E1F]">
            {mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}
          </h1>
          {searchParams.has('next') && <p role="status" className="mt-3 text-sm text-[#4B2E1F]">Inicia sesión o crea tu cuenta para ver este producto o módulo.</p>}
          <p className="text-[#7A4E2D]/70 text-sm mt-1">
            {mode === 'login' ? 'Bienvenido de nuevo a Neifit' : 'Únete a la comunidad Neifit'}
          </p>
        </div>

        <div className="card-cream p-8">
          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={loading || googleLoading || !isSupabaseConfigured}
            className="w-full flex items-center justify-center gap-3 rounded-xl border border-[#7A4E2D]/25 bg-white px-4 py-3 text-sm font-semibold text-[#4B2E1F] hover:bg-[#FFF8F2] transition-colors disabled:opacity-60"
          >
            {googleLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : (
              <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 shrink-0">
                <path fill="#4285F4" d="M22.56 12.25c0-.73-.06-1.42-.19-2.09H12v3.96h5.92a5.06 5.06 0 0 1-2.2 3.32v2.76h3.56c2.08-1.92 3.28-4.75 3.28-7.95Z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.8l-3.56-2.76c-.98.66-2.24 1.06-3.72 1.06-2.86 0-5.29-1.93-6.16-4.53H2.16v2.85A11 11 0 0 0 12 23Z" />
                <path fill="#FBBC05" d="M5.84 13.97a6.6 6.6 0 0 1 0-3.94V7.18H2.16a11 11 0 0 0 0 9.64l3.68-2.85Z" />
                <path fill="#EA4335" d="M12 5.5c1.62 0 3.06.56 4.21 1.64l3.16-3.16A10.56 10.56 0 0 0 12 1a11 11 0 0 0-9.84 6.18l3.68 2.85C6.71 7.43 9.14 5.5 12 5.5Z" />
              </svg>
            )}
            {googleLoading ? 'Abriendo Google…' : 'Continuar con Google'}
          </button>
          <p className="text-xs text-center text-[#7A4E2D] mt-2">Usa tu cuenta de Gmail o Google Workspace.</p>
          {!isSupabaseConfigured && <p className="text-xs text-center text-[#7A4E2D] mt-2">El acceso con Google aún no está disponible.</p>}
          <div className="flex items-center gap-3 my-5 text-xs text-[#7A4E2D]">
            <span className="h-px flex-1 bg-[#7A4E2D]/20" /><span>O continúa con tu correo</span><span className="h-px flex-1 bg-[#7A4E2D]/20" />
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Nombre completo *</label>
                  <input
                    type="text"
                    name="full_name"
                    value={form.full_name}
                    onChange={handleChange}
                    required
                    placeholder="María Fernanda Gómez"
                    className="w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Teléfono</label>
                  <input
                    type="tel"
                    name="phone"
                    value={form.phone}
                    onChange={handleChange}
                    placeholder="+57 300 1234567"
                    className="w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F]"
                  />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Correo electrónico *</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                placeholder="tu@correo.com"
                className="w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Contraseña *</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  minLength={6}
                  placeholder="Mínimo 6 caracteres"
                  className="w-full pl-4 pr-12 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F]"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#7A4E2D]/50 hover:text-[#7A4E2D] transition-colors"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {mode === 'login' && (
              <Link to="/recuperar-contrasena" className="block text-right text-sm text-[#7A4E2D] font-semibold hover:underline">
                ¿Olvidaste tu contraseña?
              </Link>
            )}
            {notice && <p role="status" className="text-sm text-[#4B2E1F]">{notice}</p>}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-2.5 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || googleLoading}
              className="btn-primary w-full justify-center py-3 text-base disabled:opacity-60"
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Cargando...</> : mode === 'login' ? 'Ingresar' : 'Crear cuenta'}
            </button>
          </form>

          <div className="mt-5 text-center text-sm">
            {mode === 'login' ? (
              <p className="text-[#7A4E2D]/70">
                ¿No tienes cuenta?{' '}
                <button onClick={() => setMode('register')} className="text-[#7A4E2D] font-semibold hover:underline">
                  Regístrate gratis
                </button>
              </p>
            ) : (
              <p className="text-[#7A4E2D]/70">
                ¿Ya tienes cuenta?{' '}
                <button onClick={() => setMode('login')} className="text-[#7A4E2D] font-semibold hover:underline">
                  Inicia sesión
                </button>
              </p>
            )}
          </div>

          {/* Demo role shortcuts */}
          {!isSupabaseConfigured && <div className="mt-6 pt-5 border-t border-[#7A4E2D]/15">
            <p className="text-xs text-center text-[#7A4E2D]/50 mb-3">Acceso rápido por rol (entorno de pruebas)</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { role: 'admin', label: '🛡 Admin', color: 'bg-amber-100 text-[#7A4E2D] border-amber-200' },
                { role: 'mensajeria', label: '🚛 Ruta', color: 'bg-green-100 text-[#5F8D4E] border-green-200' },
                { role: 'cliente', label: '🛍 Cliente', color: 'bg-rose-100 text-rose-700 border-rose-200' },
              ].map(({ role, label, color }) => (
                <button
                  key={role}
                  onClick={() => handleDemoLogin(role)}
                  className={`text-xs font-semibold py-2 px-1 rounded-lg border transition-all hover:opacity-80 ${color}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>}
        </div>
      </div>
    </div>
  );
}


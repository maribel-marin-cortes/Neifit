import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase, isSupabaseConfigured } from '../services/supabaseClient';
import { api } from '../services/api';
import defaults from '../services/defaultPermissions.json';

const AuthContext = createContext();

// Preconfigured demo users for testing the roles specified in AGENTS.md
const DEMO_USERS = {
  admin: {
    id: "usr-admin-1",
    email: "admin@neifit.com",
    full_name: "Administrador General",
    role: "admin",
    phone: "+57 312 7827020"
  },
  mensajeria: {
    id: "usr-delivery-1",
    email: "mensajeria@neifit.com",
    full_name: "Carlos Mensajero Neifit",
    role: "mensajeria",
    phone: "+57 300 5554433"
  },
  cliente: {
    id: "usr-cliente-1",
    email: "cliente@neifit.com",
    full_name: "María Fernanda Gómez",
    role: "cliente",
    phone: "+57 300 1234567"
  }
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    if (isSupabaseConfigured) return null;
    try {
      const saved = localStorage.getItem('neifit_current_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If Supabase is configured, listen to auth state changes
    if (isSupabaseConfigured && supabase) {
      let active = true;
      let revision = 0;
      let resolvedUserId = null;
      localStorage.removeItem('neifit_current_user');
      localStorage.removeItem('neifit_token');
      const applySession = async (session, version) => {
        if (!active || version !== revision) return;
        const sameUser = !!session?.user && session.user.id === resolvedUserId;
        if (!sameUser) setUser(null);
        try {
          if (session?.user) {
            const data = await api.getCurrentUser();
            if (active && version === revision) {
              resolvedUserId = session.user.id;
              setUser({ ...session.user, ...data });
            }
          } else {
            resolvedUserId = null;
          }
        } catch {
          if (active && version === revision) { resolvedUserId = null; setUser(null); }
        } finally {
          if (active && version === revision) setLoading(false);
        }
      };
      const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
        const version = ++revision;
        // Una renovación de la misma cuenta no debe desmontar el módulo visible.
        if (active && (!session?.user || session.user.id !== resolvedUserId)) setLoading(true);
        // No ejecutar consultas Supabase dentro del callback de autenticación.
        queueMicrotask(() => applySession(session, version));
      });
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (revision === 0) applySession(session, revision);
      }).catch(() => {
        if (active && revision === 0) setLoading(false);
      });
      const refresh = () => {
        if (!resolvedUserId) return;
        const version = ++revision;
        api.getCurrentUser().then(data => {
          if (active && version === revision) setUser(data);
        }).catch(() => { if (active && version === revision) setUser(null); });
      };
      window.addEventListener('focus', refresh);
      return () => { active = false; subscription.unsubscribe(); window.removeEventListener('focus', refresh); };
    } else {
      setLoading(false);
    }
  }, []);

  const loginWithDemoRole = (role) => {
    if (isSupabaseConfigured) throw new Error('Usa tu cuenta de Supabase para iniciar sesión.');
    const selectedUser = DEMO_USERS[role] || DEMO_USERS.cliente;
    setUser(selectedUser);
    localStorage.setItem('neifit_current_user', JSON.stringify(selectedUser));
    localStorage.setItem('neifit_token', `demo-token-${role}`);
    return selectedUser;
  };

  const login = async (email, password) => {
    if (isSupabaseConfigured && supabase) {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      return data;
    } else {
      // Local demo fallback login
      const matched = Object.values(DEMO_USERS).find(u => u.email.toLowerCase() === email.toLowerCase());
      if (matched) {
        setUser(matched);
        localStorage.setItem('neifit_current_user', JSON.stringify(matched));
        localStorage.setItem('neifit_token', `token-${matched.id}`);
        return matched;
      }
      // Default to new client
      const newUser = {
        id: `usr-${Date.now()}`,
        email,
        full_name: email.split('@')[0],
        role: "cliente",
        phone: ""
      };
      setUser(newUser);
      localStorage.setItem('neifit_current_user', JSON.stringify(newUser));
      localStorage.setItem('neifit_token', `token-${newUser.id}`);
      return newUser;
    }
  };

  const register = async (email, password, fullName, phone) => {
    if (isSupabaseConfigured && supabase) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName, phone }
        }
      });
      if (error) throw error;
      return data;
    } else {
      const newUser = {
        id: `usr-${Date.now()}`,
        email,
        full_name: fullName,
        phone,
        role: "cliente" // Default role cannot be elevated by user per AGENTS.md
      };
      setUser(newUser);
      localStorage.setItem('neifit_current_user', JSON.stringify(newUser));
      localStorage.setItem('neifit_token', `token-${newUser.id}`);
      return newUser;
    }
  };

  const logout = async () => {
    if (isSupabaseConfigured && supabase) {
      await supabase.auth.signOut();
    }
    setUser(null);
    localStorage.removeItem('neifit_current_user');
    localStorage.removeItem('neifit_token');
  };

  const isAdmin = user?.role === 'admin';
  const isMensajeria = user?.role === 'mensajeria';
  const isCliente = user?.role === 'cliente';
  const permissions = user?.permissions ?? (!isSupabaseConfigured ? defaults[user?.role] || [] : []);
  const hasPermission = code => permissions.includes(code);

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      loginWithDemoRole,
      isAdmin,
      isMensajeria,
      isCliente,
      permissions, hasPermission
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}


import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { supabase } from '../services/supabaseClient';
import { finishGoogleSignIn } from '../services/googleAuth';
import { loginDestination } from '../services/accessPolicy';

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    const url = new URL(window.location.href);
    const hash = new URLSearchParams(url.hash.slice(1));
    if (url.searchParams.has('error') || hash.has('error') || url.searchParams.has('error_code') || hash.has('error_code')) {
      setError('No se pudo completar el acceso con Google. Puede que se haya cancelado la autorización. Vuelve a intentarlo.');
    } else {
      finishGoogleSignIn(supabase).then(profile => {
        if (active) navigate(loginDestination(url.searchParams.get('next'), profile.role), { replace: true });
      }).catch(err => {
        if (active) setError(err.message || 'No se pudo completar el acceso con Google.');
      });
    }
    return () => { active = false; };
  }, [navigate]);
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16 bg-[#F6E7D8]">
      <div className="card-cream p-8 max-w-md w-full text-center">
        <img src="/logo-neifit-tropical.png" alt="Neifit" className="h-28 w-auto mx-auto mb-6" />
        <h1 className="font-display font-bold text-2xl text-[#4B2E1F] mb-4">Acceso con Google</h1>
        {error ? <>
          <p role="alert" className="text-sm text-red-700 mb-6">{error}</p>
          <Link to="/login" className="btn-primary w-full justify-center">Volver a iniciar sesión</Link>
        </> : <p role="status" className="flex items-center justify-center gap-2 text-[#4B2E1F]"><Loader2 className="w-5 h-5 animate-spin" /> Completando el acceso…</p>}
      </div>
    </div>
  );
}

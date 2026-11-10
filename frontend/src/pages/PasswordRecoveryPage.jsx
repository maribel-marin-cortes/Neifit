import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { passwordRecovery, recoveryLinkHasError } from '../services/supabaseClient';

export default function PasswordRecoveryPage({ reset = false }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [status, setStatus] = useState(reset ? 'checking' : 'ready');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [linkProblem, setLinkProblem] = useState('');

  useEffect(() => {
    let active = true;
    setError('');
    setNotice('');
    if (!reset) {
      setStatus('ready');
    } else if (!passwordRecovery || recoveryLinkHasError) {
      setLinkProblem(passwordRecovery
        ? 'Supabase rechazó el enlace. Puede haber caducado o haberse utilizado. Solicita otro enlace y abre únicamente el correo más reciente.'
        : 'La recuperación por correo aún no está disponible. Contacta con Neifit.');
      setStatus('invalid');
    } else if (passwordRecovery.hasPendingLink?.()) {
      setStatus('confirm-link');
    } else {
      setStatus('checking');
      passwordRecovery.hasRecoverySession().then(valid => {
        if (active) {
          if (!valid) setLinkProblem('No se recibió una sesión de recuperación válida. Abre el enlace original del correo, no solo la dirección de esta página. Si continúa, solicita un enlace nuevo.');
          setStatus(valid ? 'ready' : 'invalid');
        }
      }).catch(() => {
        if (active) {
          setLinkProblem('No pudimos comprobar la sesión. Revisa tu conexión y vuelve a abrir el enlace original del correo.');
          setStatus('invalid');
        }
      });
    }
    return () => { active = false; };
  }, [reset]);

  async function confirmLink() {
    setBusy(true);
    setError('');
    try {
      await passwordRecovery.confirmLink();
      setStatus('ready');
    } catch (err) {
      if (err.code === 'otp_expired') {
        setLinkProblem('Supabase indica que este enlace ha caducado o ya fue utilizado. Solicita otro enlace y abre el correo más reciente.');
        setStatus('invalid');
      } else if (err.status === 429) {
        setError('Se alcanzó el límite temporal de verificaciones. Espera antes de intentarlo otra vez.');
      } else {
        setError('No se pudo verificar el enlace. Comprueba tu conexión; si continúa, solicita uno nuevo.');
      }
    } finally { setBusy(false); }
  }

  async function submit(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    try {
      if (!passwordRecovery) throw new Error('La recuperación de contraseña aún no está disponible. Contacta con Neifit.');
      if (reset) {
        await passwordRecovery.update(password, confirmation);
        setPassword('');
        setConfirmation('');
        setStatus('success');
      } else {
        const message = await passwordRecovery.request(email);
        setNotice(message);
        setStatus('sent');
      }
    } catch (err) {
      if (err.status === 429 || err.code === 'over_email_send_rate_limit') {
        setError('Se alcanzó el límite temporal de solicitudes. Evita volver a enviarlas de inmediato. Inténtalo más tarde o contacta con Neifit si el problema continúa.');
      } else if (!reset) {
        setError(passwordRecovery ? 'No se pudo enviar el enlace. Inténtalo más tarde o contacta con Neifit.' : err.message);
      } else if (['weak_password', 'same_password'].includes(err.code)) {
        setError('Elige una contraseña diferente y más segura, de al menos 8 caracteres.');
      } else {
        setError(err.message || 'No se pudo actualizar la contraseña. Solicita un enlace nuevo.');
      }
    } finally {
      setBusy(false);
    }
  }

  const inputClass = 'w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F]';
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16 bg-[#F6E7D8]">
      <div className="w-full max-w-md">
        <Link to="/" aria-label="Volver al inicio de Neifit">
          <img src="/logo-neifit-tropical.png" alt="Neifit" className="h-28 w-auto mx-auto mb-6" />
        </Link>
        <div className="card-cream p-8">
          <h1 className="font-display font-bold text-2xl text-[#4B2E1F] mb-3">
            {reset ? 'Nueva contraseña' : 'Recuperar contraseña'}
          </h1>
          {status === 'checking' ? (
            <p role="status" className="flex items-center gap-2 text-[#4B2E1F]"><Loader2 className="w-4 h-4 animate-spin" /> Verificando enlace…</p>
          ) : status === 'confirm-link' ? (
            <div className="space-y-4">
              <p className="text-[#4B2E1F]">Pulsa continuar para verificar el enlace del correo y elegir tu nueva contraseña.</p>
              {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
              <button type="button" disabled={busy} onClick={confirmLink} className="btn-primary justify-center w-full disabled:opacity-60">
                {busy ? <><Loader2 className="w-4 h-4 animate-spin" /> Verificando…</> : 'Continuar con la recuperación'}
              </button>
            </div>
          ) : status === 'invalid' ? (
            <div className="space-y-4">
              <p role="alert" className="text-[#4B2E1F]">{linkProblem}</p>
              <Link to="/recuperar-contrasena" className="btn-primary justify-center w-full">Solicitar otro enlace</Link>
            </div>
          ) : status === 'success' ? (
            <div className="space-y-4">
              <p role="status" className="text-[#4B2E1F]">Tu contraseña se actualizó correctamente. Ya puedes iniciar sesión con la nueva contraseña.</p>
              <Link to="/login" className="btn-primary justify-center w-full">Iniciar sesión</Link>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              {!reset ? (
                <>
                  <p className="text-sm text-[#4B2E1F]">Escribe el correo con el que creaste tu cuenta y te enviaremos un enlace para elegir una contraseña nueva.</p>
                  <div>
                    <label htmlFor="recovery-email" className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Correo electrónico</label>
                    <input id="recovery-email" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} className={inputClass} />
                  </div>
                </>
              ) : (
                <>
                  <p className="text-sm text-[#4B2E1F]">Elige una contraseña de al menos 8 caracteres. Puedes usar una frase larga con letras, números y símbolos.</p>
                  <div>
                    <label htmlFor="new-password" className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Nueva contraseña</label>
                    <input id="new-password" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={e => setPassword(e.target.value)} className={inputClass} />
                  </div>
                  <div>
                    <label htmlFor="confirm-password" className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Confirmar nueva contraseña</label>
                    <input id="confirm-password" type="password" autoComplete="new-password" minLength={8} required value={confirmation} onChange={e => setConfirmation(e.target.value)} className={inputClass} />
                  </div>
                </>
              )}
              {notice && <p role="status" className="text-sm text-green-800">{notice}</p>}
              {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
              <button disabled={busy || !passwordRecovery || status === 'sent'} type="submit" className="btn-primary justify-center w-full py-3 disabled:opacity-60">
                {busy ? <><Loader2 className="w-4 h-4 animate-spin" /> Procesando…</> : reset ? 'Guardar nueva contraseña' : status === 'sent' ? 'Solicitud enviada' : 'Enviar enlace de recuperación'}
              </button>
              {!passwordRecovery && <p role="status" className="text-sm text-[#4B2E1F]">La recuperación por correo aún no está disponible. Contacta con Neifit.</p>}
            </form>
          )}
          <Link to="/login" className="block text-center mt-6 text-sm text-[#7A4E2D] font-semibold hover:underline">Volver a iniciar sesión</Link>
        </div>
      </div>
    </div>
  );
}

export const RECOVERY_PATH = '/restablecer-contrasena';
const STORAGE_KEY = 'neifit_recovery_user';
export const RECOVERY_SENT_MESSAGE = 'Si existe una cuenta con ese correo, recibirás un enlace para restablecer tu contraseña. Revisa también la carpeta de spam.';

export function hasRecoveryLinkError(href) {
  const url = new URL(href);
  const hash = new URLSearchParams(url.hash.slice(1));
  return ['error', 'error_code'].some(key => url.searchParams.has(key) || hash.has(key));
}

export function isRecoveryCallback(href) {
  const url = new URL(href);
  const hash = new URLSearchParams(url.hash.slice(1));
  return url.pathname === RECOVERY_PATH && !hasRecoveryLinkError(href)
    && (hash.get('type') === 'recovery' || url.searchParams.has('code'));
}

export function readRecoveryTokenHash(href) {
  const url = new URL(href);
  if (url.pathname !== RECOVERY_PATH || hasRecoveryLinkError(href) || url.searchParams.get('type') !== 'recovery') return null;
  return url.searchParams.get('token_hash') || null;
}

export function createPasswordRecovery(auth, { origin, storage, callbackExpected = false, eventTimeoutMs = 5000, tokenHash = null, clearRecoveryUrl = () => {} }) {
  let recoveryUserId = null;
  let pendingTokenHash = tokenHash;
  let verification = null;
  const recoveryWaiters = new Set();
  try { recoveryUserId = storage?.getItem(STORAGE_KEY) || null; } catch { /* Memoria como respaldo. */ }
  function setRecoveryUser(id) {
    recoveryUserId = id;
    if (id) for (const finish of [...recoveryWaiters]) finish();
    try {
      if (id) storage?.setItem(STORAGE_KEY, id);
      else storage?.removeItem(STORAGE_KEY);
    } catch { /* La recuperación actual funciona sin almacenamiento. */ }
  }
  // Suscribir al crear el cliente, antes de montar React: evita perder el evento
  // que emite Supabase al procesar el enlace recibido por correo.
  const { data: { subscription } } = auth.onAuthStateChange((event, session) => {
    if (event === 'PASSWORD_RECOVERY') setRecoveryUser(session?.user?.id || null);
    if (event === 'SIGNED_OUT' || (event === 'SIGNED_IN' && session?.user?.id !== recoveryUserId)) setRecoveryUser(null);
  });

  async function hasRecoverySession() {
    const { data: { session }, error } = await auth.getSession();
    if (error) throw error;
    // auth-js guarda la sesión y resuelve initialize/getSession ANTES de
    // notificar PASSWORD_RECOVERY mediante setTimeout(..., 0).
    // Esperar el evento únicamente si la navegación inicial era de recuperación;
    // tener una sesión normal o escribir type=recovery no concede autorización.
    if (session?.user?.id && !recoveryUserId && callbackExpected) {
      await new Promise(resolve => {
        const finish = () => {
          clearTimeout(timer);
          recoveryWaiters.delete(finish);
          resolve();
        };
        const timer = setTimeout(finish, eventTimeoutMs);
        recoveryWaiters.add(finish);
      });
    }
    return Boolean(session?.user?.id && session.user.id === recoveryUserId);
  }

  return {
    hasRecoverySession,
    hasPendingLink: () => Boolean(pendingTokenHash),
    async confirmLink() {
      if (verification) return verification;
      if (!pendingTokenHash) throw new Error('No se recibió un enlace de recuperación verificable.');
      verification = (async () => {
        const { data, error } = await auth.verifyOtp({ token_hash: pendingTokenHash, type: 'recovery' });
        if (error) throw error;
        if (!data?.session?.user?.id) throw new Error('No se pudo iniciar la sesión de recuperación.');
        setRecoveryUser(data.session.user.id);
        pendingTokenHash = null;
        clearRecoveryUrl();
      })();
      try { await verification; } catch (error) { verification = null; throw error; }
    },
    dispose: () => {
      subscription.unsubscribe();
      for (const finish of [...recoveryWaiters]) finish();
    },
    async request(email) {
      const { error } = await auth.resetPasswordForEmail(email.trim(), {
        redirectTo: new URL(RECOVERY_PATH, origin).href,
      });
      // No revelar si una dirección tiene cuenta registrada.
      if (error && error.code !== 'user_not_found') throw error;
      return RECOVERY_SENT_MESSAGE;
    },
    async update(password, confirmation) {
      if (password.length < 8) throw new Error('Usa una contraseña de al menos 8 caracteres.');
      if (password !== confirmation) throw new Error('Las contraseñas no coinciden.');
      if (!await hasRecoverySession()) throw new Error('El enlace no es válido o ha caducado. Solicita uno nuevo.');
      const { error } = await auth.updateUser({ password });
      if (error) throw error;
      setRecoveryUser(null);
      // El cambio ya está confirmado. Un fallo al cerrar sesión no debe
      // presentarse como si hubiera fallado el cambio de contraseña.
      try { await auth.signOut({ scope: 'local' }); } catch { /* Cambio realizado. */ }
    },
  };
}

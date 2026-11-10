import { createClient } from '@supabase/supabase-js';
import { createPasswordRecovery, hasRecoveryLinkError, isRecoveryCallback, readRecoveryTokenHash } from './passwordRecovery';

export const recoveryLinkHasError = hasRecoveryLinkError(window.location.href);
// Capturar antes de crear el cliente: Supabase limpia los tokens de la URL.
const callbackExpected = isRecoveryCallback(window.location.href);
const tokenHash = readRecoveryTokenHash(window.location.href);

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

export const passwordRecovery = supabase
  ? createPasswordRecovery(supabase.auth, {
    origin: window.location.origin, storage: window.sessionStorage, callbackExpected, tokenHash,
    clearRecoveryUrl: () => {
      const url = new URL(window.location.href);
      url.searchParams.delete('token_hash');
      url.searchParams.delete('type');
      window.history.replaceState(window.history.state, '', url.pathname + url.search);
    },
  })
  : null;


export const GOOGLE_CALLBACK_PATH = '/auth/callback';
import { safeReturnTo } from './accessPolicy.js';

export async function startGoogleSignIn(auth, origin, returnTo) {
  if (!auth) throw new Error('El acceso con Google aún no está disponible.');
  const callback = new URL(GOOGLE_CALLBACK_PATH, origin);
  if (returnTo) callback.searchParams.set('next', safeReturnTo(returnTo));
  const { data, error } = await auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: callback.href,
      queryParams: { prompt: 'select_account' },
      skipBrowserRedirect: true,
    },
  });
  if (error) throw error;
  if (!data?.url) throw new Error('No se pudo iniciar el acceso con Google.');
  return data.url;
}

export async function finishGoogleSignIn(client) {
  if (!client) throw new Error('El acceso con Google aún no está disponible.');
  const { data: { session }, error } = await client.auth.getSession();
  if (error) throw error;
  if (!session?.user?.id) throw new Error('No se completó el acceso con Google. Vuelve a intentarlo desde el inicio de sesión.');
  // El rol proviene de perfiles; no se toma de los datos de Google.
  const { data: profile, error: profileError } = await client.from('perfiles')
    .select('id,full_name:nombre_completo,email:correo,phone:telefono,role:rol')
    .eq('id', session.user.id).single();
  if (profileError || !profile || profile.id !== session.user.id) {
    throw new Error('Tu cuenta se autenticó, pero no pudimos cargar su perfil. Contacta con Neifit.');
  }
  return profile;
}

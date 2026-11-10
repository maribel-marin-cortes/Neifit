# Neifit: acceso con Google y Gmail

La pantalla `/login` incluye **Continuar con Google**, también disponible al crear cuenta. Permite autenticarse con Gmail o Google Workspace. El correo/contraseña de Neifit sigue disponible; no se solicita la contraseña de Google en Neifit ni acceso a mensajes del buzón.

El código inicia OAuth mediante Supabase y regresa a `/auth/callback`, donde comprueba sesión y perfil. El trigger SQL ya preparado crea a los usuarios nuevos como `cliente`, sin permitir que Google o sus metadatos asignen roles administrativos.

## Estado y configuración pendiente

En la comprobación de este cambio, la configuración pública de Supabase indicó `external.google = false`. El botón está implementado pero el acceso real requiere habilitar el proveedor. No se modificaron cuentas Google, credenciales ni el panel remoto.

## 1. Crear las credenciales Google

1. Abre https://console.cloud.google.com/ y selecciona o crea un proyecto para Neifit.
2. Abre **Google Auth Platform**. Si no has iniciado la configuración, completa **Get started**.
3. En **Branding**, introduce Neifit como nombre de aplicación y tus correos reales de soporte/contacto. No inventes URLs de políticas: agrega las direcciones aprobadas cuando estén publicadas.
4. En **Audience**, elige **External** si se permitirá acceso a clientes fuera de tu organización Google Workspace. Si la aplicación queda en pruebas, añade las cuentas de prueba en **Test users**. La opción Internal restringe el acceso a una organización Workspace.
5. En **Data Access**, configura únicamente los permisos básicos `openid`, correo y perfil (`userinfo.email` y `userinfo.profile`). No se necesitan permisos para leer o enviar Gmail.
6. En **Clients → Create client**, elige **Web application** y un nombre descriptivo, por ejemplo `Neifit web`.
7. En **Authorized JavaScript origins**, agrega los orígenes locales que utilizarás:

```text
http://localhost:5173
http://127.0.0.1:5173
```

8. En **Authorized redirect URIs**, agrega EXACTAMENTE el callback de tu proyecto Supabase:

```text
https://anozyfhqmtrzudxdtetq.supabase.co/auth/v1/callback
```

9. Guarda el cliente y copia **Client ID** y **Client Secret**. El secreto no se coloca en React, en `VITE_*`, en git ni en el chat.

## 2. Habilitar Google en Supabase

1. Entra en https://supabase.com/dashboard/project/anozyfhqmtrzudxdtetq.
2. Abre **Authentication → Sign In / Providers → Google** (en algunas versiones aparece como **Providers**).
3. Activa **Enable Sign in with Google**.
4. Introduce el **Client ID** y **Client Secret** de Google. Conserva activada la validación del nonce si el panel muestra esa opción; este flujo OAuth no requiere desactivarla.
5. Comprueba que el callback mostrado coincide exactamente con el configurado en Google Cloud y guarda.

## 3. Permitir el regreso a Neifit

1. En **Authentication → URL Configuration**, conserva como Site URL local `http://127.0.0.1:5173` si esa es la dirección utilizada.
2. Añade estas URL a **Redirect URLs**, conservando las que ya existen para recuperar contraseñas:

```text
http://127.0.0.1:5173/auth/callback
http://localhost:5173/auth/callback
```

3. Guarda los cambios.

No confundas las dos redirecciones: Google vuelve a `https://...supabase.co/auth/v1/callback`; después Supabase vuelve a `http://...:5173/auth/callback`. No agregues `localhost:5173/auth/callback` como sustituto del callback de Supabase en Google Cloud.

## 4. Comprobar variables y perfil

1. El frontend utiliza las variables existentes `VITE_SUPABASE_URL` y `VITE_SUPABASE_PUBLISHABLE_KEY`. No requiere un Client Secret de Google en `.env`.
2. Debe haberse ejecutado `supabase/neifit_inicial.sql`, que crea `profiles` y su trigger de alta automática con rol cliente.
3. Si cambiaste `.env`, reinicia `iniciar-frontend.ps1`. Los cambios guardados solo en los paneles no requieren recompilar el código.

## 5. Probar el acceso

1. Abre http://127.0.0.1:5173/login.
2. Pulsa **Continuar con Google**.
3. Elige una cuenta. Si Google Auth Platform está en modo Testing, usa una cuenta añadida como usuario de prueba.
4. Autoriza el acceso básico a perfil/correo si Google lo solicita.
5. Debes regresar a Neifit. Comprueba la cuenta en **Supabase → Authentication → Users** y su perfil en **Table Editor → profiles**.
6. Verifica que el rol inicial sea `cliente`; la asignación de administrador sigue haciéndose mediante el procedimiento autorizado en Supabase.
7. Cierra sesión y repite para comprobar el acceso de una cuenta existente.

Si accedes con Google, la contraseña de esa cuenta se administra en Google. No confundas recuperarla con crear/restablecer una contraseña local de Neifit.

## Diagnóstico

| Mensaje o síntoma | Revisar |
|---|---|
| `Unsupported provider` o proveedor no habilitado | Activar Google y guardar credenciales en Supabase |
| `redirect_uri_mismatch` | URI Google exactamente `https://anozyfhqmtrzudxdtetq.supabase.co/auth/v1/callback` |
| `Access blocked` en pruebas | Audience y Test users en Google Auth Platform |
| Regresa al inicio equivocado | Redirect URLs y origen actual del frontend |
| Cuenta autenticada, pero no carga perfil | Tabla `profiles`, trigger y política de lectura propia |
| Se canceló la autorización | Volver a login y repetir voluntariamente |

Al publicar, agrega el origen HTTPS y `/auth/callback` de tu dominio real en los lugares correspondientes y configura el alojamiento para resolver esa ruta SPA. Revisa las exigencias de publicación/branding de Google antes de abrir el acceso a clientes generales.

Fuentes oficiales: [Google con Supabase](https://supabase.com/docs/guides/auth/social-sign-in/auth-google) y [redirecciones](https://supabase.com/docs/guides/auth/redirect-urls).

# Recuperación de contraseña de Neifit: configuración y prueba

## Qué quedó implementado

- En `/login`: enlace **¿Olvidaste tu contraseña?**.
- En `/recuperar-contrasena`: formulario para solicitar un enlace por correo.
- En `/restablecer-contrasena`: validación de la sesión de recuperación y formulario de nueva contraseña con confirmación.
- Supabase envía/verifica el enlace y guarda la contraseña; no se guarda en tablas `public`, `.env` ni en el backend.
- Tras guardar, se limpia el estado de recuperación y se intenta cerrar la sesión local para volver a entrar con la nueva contraseña.
- El mensaje de solicitud no revela si un correo tiene cuenta. Ese mensaje tampoco garantiza la entrega: se comprueba en la bandeja de entrada y logs del proveedor.

## 1. Comprobar el proyecto y la cuenta

1. Abre https://supabase.com/dashboard/project/anozyfhqmtrzudxdtetq.
2. En **Authentication → Users**, comprueba que existe el usuario cuyo correo vas a utilizar.
3. Usa un correo que controles y completa la confirmación de registro, si está habilitada.
4. El usuario y la aplicación deben pertenecer al mismo proyecto Supabase.

No hace falta modificar `DATABASE_URL`, el SQL, el rol del usuario ni la clave `service_role` para enviar la recuperación. La aplicación usa Supabase Auth con la clave pública del frontend.

## 2. Revisar las variables del frontend

En `frontend/.env` deben estar configuradas:

```dotenv
VITE_SUPABASE_URL=https://anozyfhqmtrzudxdtetq.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=TU_CLAVE_PUBLICA_EXISTENTE
```

Conserva tu clave ya configurada; el texto anterior es un marcador. No agregues contraseñas SMTP ni claves privadas a `VITE_*`. Reinicia Vite si cambias `.env`.

## 3. Autorizar las direcciones de retorno

1. En Supabase abre **Authentication → URL Configuration**.
2. Para estas pruebas locales, configura **Site URL**:

```text
http://127.0.0.1:5173
```

3. En **Redirect URLs**, agrega estas direcciones exactas:

```text
http://127.0.0.1:5173/restablecer-contrasena
http://localhost:5173/restablecer-contrasena
```

4. Conserva las URL de registro que ya necesite la aplicación y guarda los cambios.
5. Abre Neifit siempre con la dirección escogida. El código construye el destino utilizando el origen actual del navegador; `localhost` y `127.0.0.1` son orígenes diferentes.

Cuando se publique la web, agrega también `https://TU_DOMINIO_REAL/restablecer-contrasena` y usa el dominio público como Site URL. El alojamiento debe servir la SPA al abrir directamente esa ruta. No uses una URL local para clientes: si abren el correo desde otro dispositivo, `127.0.0.1` apunta a ese otro dispositivo, no a tu computador.

Referencia: [URL de redirección de Supabase](https://supabase.com/docs/guides/auth/redirect-urls).

## 4. Elegir cómo enviar correos

### Prueba limitada con el correo predeterminado de Supabase

El servicio predeterminado solo entrega a direcciones del equipo de la organización del proyecto y tiene límites muy reducidos. No sirve como envío general a clientes. Puedes realizar una prueba con una dirección que ya pertenezca a tu equipo; no agregues clientes como miembros de la organización para eludir esa restricción. En el servicio predeterminado se documenta un límite de dos correos por hora por proyecto, compartido por los flujos que envían correo: consulta el límite vigente en tu panel.

### Envío a clientes mediante SMTP propio

Configura un proveedor que permita enviar correo transaccional con un remitente autorizado. Puede ser tu proveedor actual si ofrece SMTP apropiado. Necesitarás remitente, host, puerto, usuario y contraseña SMTP. El ejemplo siguiente utiliza Resend porque su documentación incluye la conexión directa con Supabase; no es obligatorio usarlo.

Referencias: [SMTP en Supabase](https://supabase.com/docs/guides/auth/auth-smtp) y [límites de Auth](https://supabase.com/docs/guides/auth/rate-limits).

## 5. Ejemplo detallado: configurar Resend SMTP

1. Crea tu cuenta en Resend.
2. Debes disponer de un dominio que controles para enviar a destinatarios generales. En **Domains**, agrega ese dominio o subdominio.
3. En el administrador DNS de tu dominio agrega exactamente los registros que te indique Resend. No inventes los valores ni borres registros de correo existentes; integra los que correspondan según su verificación.
4. Espera a que el proveedor indique que el dominio está verificado.
5. En **API Keys**, crea una clave con permiso de envío para el dominio correspondiente. Guárdala de forma privada.
6. Vuelve a Supabase y entra en **Authentication → Email**, dentro de la sección **Notifications**; abre **SMTP Settings**. En algunas versiones del panel aparece directamente como **Custom SMTP**.
7. Activa el SMTP personalizado y completa:

| Campo | Valor |
|---|---|
| Sender name | `Neifit` |
| Sender email | Una dirección autorizada de TU dominio verificado |
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | La API key de Resend creada en el paso 5 |

8. Guarda la configuración. La contraseña SMTP se configura en Supabase; no se añade a React, no es la clave pública Supabase y no es la contraseña de PostgreSQL.
9. Revisa las restricciones de destinatarios, dominio y cuota de tu proveedor. Su dominio de pruebas no sustituye a un remitente de dominio verificado para enviar a clientes generales.
10. Desactiva el seguimiento de clics en esos correos de autenticación si tu proveedor lo habilita: reescribir los enlaces puede interferir con la recuperación.

Fuente de los parámetros: [guía oficial Resend + Supabase SMTP](https://resend.com/docs/send-with-supabase-smtp).

## 6. Configurar el mensaje de recuperación

1. En **Authentication → Email**, busca las plantillas (**Templates** o **Email Templates**).
2. Selecciona **Reset Password**, no **Confirm signup** ni **Magic Link**.
3. Escribe un asunto, por ejemplo: **Restablece tu contraseña de Neifit**.
4. Usa el contenido de `supabase/templates/reset_password.html`. Esta versión abre Neifit primero y verifica el código solo al pulsar «Continuar con la recuperación»:

```html
<h2>Recupera el acceso a Neifit</h2>
<p>Recibimos una solicitud para restablecer tu contraseña.</p>
<p><a href="{{ .RedirectTo }}?token_hash={{ .TokenHash }}&amp;type=recovery">Elegir una nueva contraseña</a></p>
<p>En la página que se abra, pulsa «Continuar con la recuperación».</p>
<p>Si no hiciste esta solicitud, puedes ignorar este mensaje.</p>
<p>Equipo Neifit</p>
```

5. Conserva `{{ .RedirectTo }}`, `{{ .TokenHash }}` y `type=recovery` exactamente como aparecen. Solicita el enlace desde Neifit para que se incluya `RedirectTo`. No reemplaces el enlace por una dirección fija sin código. La plantilla anterior con `{{ .ConfirmationURL }}` sigue siendo compatible, pero verifica el enlace antes de llegar a la aplicación; algunos sistemas de correo pueden consumirlo al inspeccionarlo. La plantilla nueva evita que una mera carga de la página ejecute la verificación.
6. Guarda la plantilla.
7. Revisa la configuración de caducidad de enlaces de correo (**Email OTP Expiration**) en los ajustes de Email de Auth. Usa el tiempo configurado en tu proyecto; no presupongas que un enlace antiguo seguirá vigente. Los enlaces de recuperación son de un solo uso.

Referencia: [plantillas de correo Supabase](https://supabase.com/docs/guides/auth/auth-email-templates).

## 7. Iniciar la aplicación

Desde la raíz del proyecto, abre dos terminales:

```powershell
# Terminal 1
.\iniciar-backend.ps1
```

```powershell
# Terminal 2
.\iniciar-frontend.ps1
```

Si ya estaban ejecutándose con el código actual, Vite carga los cambios automáticamente. Si modificaste variables de entorno, detén con Ctrl+C y reinicia. La recuperación la procesa Supabase Auth: no depende de un endpoint de correo FastAPI.

## 8. Prueba completa con tu correo real

1. Abre http://127.0.0.1:5173/login.
2. Haz clic en **¿Olvidaste tu contraseña?**.
3. Escribe el correo de la cuenta que comprobaste en Authentication → Users.
4. Pulsa **Enviar enlace de recuperación** una sola vez y espera la respuesta.
5. El mensaje será genérico por privacidad; revisa la bandeja de entrada, spam y promociones.
6. En la primera prueba local, abre el correo en el mismo computador donde ejecutas Neifit y usa el enlace más reciente.
7. Haz clic en **Elegir una nueva contraseña**. Con la plantilla nueva se abre `/restablecer-contrasena`: pulsa **Continuar con la recuperación** para verificar el código en Supabase. Con la plantilla anterior, Supabase verifica antes de redirigir. Solo se muestra el formulario cuando existe una sesión de recuperación válida.
8. Escribe la nueva contraseña dos veces. La interfaz exige al menos ocho caracteres; si configuraste requisitos mayores en Supabase, también debes cumplirlos.
9. Pulsa **Guardar nueva contraseña** y espera el mensaje de éxito.
10. Entra en **Iniciar sesión** y comprueba la nueva contraseña.
11. Comprueba también que la contraseña anterior ya no permite entrar. Cambiar la contraseña no elimina productos, pedidos ni el perfil.
12. Si vuelves a usar el mismo enlace o caducó, solicita uno nuevo. Una dirección escrita manualmente sin enlace válido no habilita el formulario de recuperación.

## 9. Si el correo no llega

Un estado HTTP 429 significa que se alcanzó un límite. Revisa la ruta de la solicitud y el código en su respuesta: `/auth/v1/recover` corresponde al envío del enlace; `/auth/v1/token` corresponde a acceso/renovación y no implica necesariamente una cuota de correo. La recuperación tiene por defecto una separación mínima de 60 segundos por usuario; el proveedor de correo predeterminado tiene además una cuota compartida de dos correos por hora por proyecto. Por eso esperar unos minutos no siempre es suficiente. Revisa Authentication → Rate Limits y los logs antes de repetir intentos; recargar o reiniciar Neifit no reinicia los límites de Supabase.

1. Comprueba que el usuario existe en el proyecto correcto y que escribiste bien su correo.
2. Comprueba si estás usando el servicio predeterminado: los destinatarios externos al equipo requieren SMTP propio.
3. Revisa **Authentication → Logs** y los logs de correo de tu proveedor. Distingue envío aceptado de entrega final; busca errores de credenciales, remitente o cuota.
4. Comprueba el dominio verificado y que el remitente pertenezca a ese dominio.
5. Revisa spam/promociones y espera antes de volver a pedir un enlace si alcanzaste el límite.
6. Si el enlace abre el inicio en vez del formulario, revisa Redirect URLs y que la plantilla sea exactamente una de las variantes documentadas, conservando el código de verificación. La dirección `/restablecer-contrasena` sola no permite recuperar una contraseña.
7. Si aparece `otp_expired`, pide otro enlace y usa solo el más reciente. Algunos escáneres de seguridad del correo pueden consumir enlaces; revisa también la documentación del proveedor y desactiva reescritura/seguimiento de enlaces.
8. Si aparece una dirección local inaccesible desde el teléfono, abre el correo en el computador de desarrollo o publica la aplicación con una URL HTTPS accesible.

## Validación realizada y pendiente

Revisión posterior: se distingue una sesión ausente, un rechazo explícito de Supabase y un fallo al comprobar la sesión, en lugar de mostrar siempre «caducado». Se añadió soporte para `token_hash` con `verifyOtp({type: 'recovery'})` tras un clic explícito; no verifica ni envía correos al cargar la página. Pruebas locales: 24 pruebas frontend, compilación y navegador con el SDK instalado y respuestas Supabase interceptadas. El flujo anterior con `ConfirmationURL` continúa probado y compatible. No se confirmó la causa exacta del enlace del usuario ni se cambió la plantilla remota: la instalación de la plantilla nueva y la entrega real siguen pendientes.

Corrección de sincronización: el SDK instalado guarda la sesión y puede resolver `getSession()` antes de emitir `PASSWORD_RECOVERY` en un temporizador. La aplicación ahora detecta el callback antes de que Supabase limpie la URL y espera el evento real, con un límite de tiempo. No habilita el formulario por tener solamente una sesión normal o un parámetro `type=recovery`. Se añadieron pruebas para este orden de eventos. Si estabas en la pantalla de enlace inválido, recarga con Ctrl+F5; si no queda una sesión de recuperación válida, solicita otro enlace y abre el correo más reciente en el computador de desarrollo.

Se añadieron pruebas automatizadas del destino del enlace, errores de envío, confirmación de contraseña, rechazo de sesiones normales, recuperación válida y enlaces caducados. La prueba de navegador utiliza Supabase simulado para no enviar correos ni cambiar contraseñas reales. La entrega real y el enlace recibido deben probarse después de configurar tu panel y tu proveedor; no se modificó tu SMTP ni se envió ningún correo real.

Detalles de las API utilizadas: [resetPasswordForEmail](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail) y [updateUser](https://supabase.com/docs/reference/javascript/auth-updateuser).

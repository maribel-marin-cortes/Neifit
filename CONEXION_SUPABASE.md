# Neifit: SQL y conexión Supabase

Para habilitar el botón «Continuar con Google» (Gmail y Google Workspace), consulta `ACCESO_GOOGLE.md`. Requiere un cliente OAuth en Google Cloud y activar el proveedor Google en Supabase; no se agregan secretos de Google al frontend.

Para habilitar y probar el envío de enlaces de recuperación de contraseña, sigue `RECUPERACION_CONTRASENA.md`. Incluye Redirect URLs, SMTP, plantilla Reset Password y prueba de entrega. No requiere cambios SQL ni agregar contraseñas a las tablas públicas.

Guía del 7 de noviembre de 2026. No necesitas compartir claves en el chat.

## 1. Crear el proyecto

Entra en https://supabase.com/dashboard → **New project**, elige tu organización, nombre `neifit` y región. Guarda la contraseña de base de datos y espera a que el proyecto esté disponible.

El script está diseñado para un proyecto nuevo sin tablas Neifit existentes. Si ya hay tablas con estos nombres, primero hay que comparar sus estructuras; no borres datos para ejecutar esta instalación.

## 2. Ejecutar el SQL

1. Abre `supabase/neifit_inicial.sql` en este proyecto y copia TODO su contenido.
2. En Supabase abre **SQL Editor → New query**.
3. Pega el contenido y pulsa **Run**.
4. La consulta final debe mostrar 14 tablas con `rowsecurity = true`.
5. En otra consulta ejecuta `supabase/verificar_seguridad.sql`: revisa los conteos y que no aparezcan excepciones `FALLO`.

Se crean 14 tablas, índices, restricciones, RLS, perfiles automáticos de cliente, 3 categorías, 5 contenidos institucionales, 6 valores y los buckets `products` (público) y `evidence` (privado). No se cargan productos, precios, existencias, usuarios ni pedidos ficticios.

Ejecuta el instalador una sola vez. Las modificaciones posteriores serán migraciones nuevas. Si falla antes de `COMMIT`, no se confirma la transacción. Revisa el primer error; si el editor indica una transacción abortada, ejecuta `ROLLBACK;` antes de reintentar el script corregido.

## 3. Obtener URL y claves

Consulta el diálogo **Connect** y **Settings → API Keys** del proyecto:

| Dato | Destino |
|---|---|
| Project URL: `https://TU_PROJECT_REF.supabase.co` | Frontend y backend |
| Publishable key: `sb_publishable_...` | Variable pública del frontend |
| Clave legacy **service_role**, JWT que suele empezar por `eyJ...` | Exclusivamente backend |

Para el backend actual usa `service_role` de la pestaña de claves legacy. No es la contraseña PostgreSQL, `anon`, el JWT signing secret ni la clave moderna `sb_secret_...`: el código actual envía la clave como Bearer JWT, por lo que una `sb_secret_...` necesita adaptar ese encabezado primero. Nunca pongas `service_role` en variables `VITE_*`.

Referencia: https://supabase.com/docs/guides/getting-started/api-keys

## 4. Configurar autenticación

1. En **Authentication**, comprueba que el proveedor Email esté habilitado.
2. En **URL Configuration**, configura **Site URL** como `http://127.0.0.1:5173`.
3. Agrega `http://127.0.0.1:5173/` y, si también lo usas, `http://localhost:5173/` a las redirecciones permitidas.
4. Mantén la confirmación de correo: tras registrarte abre el enlace recibido y luego inicia sesión.
5. En **JWT Signing Keys**, comprueba que los tokens nuevos usen una clave asimétrica ES256 o RS256. El backend valida esos algoritmos con JWKS. Si tu proyecto antiguo usa HS256, sigue la migración de claves oficial antes de probarlo; no desactives la verificación de firma.

Referencias: https://supabase.com/docs/guides/auth/redirect-urls y https://supabase.com/docs/guides/auth/signing-keys

## 5. Editar frontend/.env

Sustituye los valores del archivo existente:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=https://TU_PROJECT_REF.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_TU_CLAVE_PUBLICA
```

Usa los valores de tu proyecto. No agregues `/auth/v1` a `VITE_SUPABASE_URL`.

## 6. Editar backend/.env

Usa el mismo proyecto que en el frontend y conserva las demás variables existentes:

```dotenv
SUPABASE_URL=https://TU_PROJECT_REF.supabase.co
SUPABASE_JWT_ISSUER=https://TU_PROJECT_REF.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://TU_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=TU_JWT_LEGACY_SERVICE_ROLE
DATABASE_URL=
ALLOWED_ORIGINS=["http://127.0.0.1:5173","http://localhost:5173"]
APP_ENV=development
ENABLE_DEMO_AUTH=false
DEBUG=true
```

`DATABASE_URL` puede quedar vacía: perfiles y servicios comerciales utilizan Supabase REST y RPC mediante `httpx`. Para activar los servicios comerciales debes aplicar la migración 0005 siguiendo **PERSISTENCIA_SUPABASE.md**.

## 7. Reiniciar los servicios

Detén los servidores anteriores con Ctrl+C. Abre dos terminales PowerShell en la raíz del proyecto:

```powershell
# Terminal 1: autenticación real
.\iniciar-backend.ps1
```

```powershell
# Terminal 2
.\iniciar-frontend.ps1
```

Abre http://127.0.0.1:5173. La documentación API está en http://127.0.0.1:8000/docs. Reinicia ambos servidores después de cambiar `.env`.

Para volver a demo, deja vacías las variables Supabase de ambos `.env`, reinicia Vite y ejecuta `.\iniciar-backend.ps1 -Demo`. Con Supabase configurado se ocultan los botones demo y la API rechaza esos tokens.

## 8. Crear cuenta y primer administrador

1. En Neifit abre **Crear cuenta**, usa tu correo real y confirma el correo recibido.
2. Inicia sesión. El usuario debe aparecer en **Authentication → Users** y en **Table Editor → profiles**, con la misma UUID y `role = cliente`.
3. Para localizar el identificador, ejecuta en SQL Editor:

```sql
select id, email, full_name, role
from public.profiles
order by created_at desc;
```

4. Copia la UUID de TU cuenta y sustituye el marcador:

```sql
update public.profiles
set role = 'admin'
where id = 'REEMPLAZAR_POR_UUID_DE_TU_CUENTA'::uuid
returning id, email, role;
```

Debe devolver exactamente tu cuenta con rol `admin`. Cierra sesión y vuelve a entrar para actualizar el rol en la interfaz. Para designar un mensajero, usa el mismo procedimiento con su UUID y `role = 'mensajeria'`. No cambies los roles internos PostgreSQL (`anon`, `authenticated`, `service_role`).

El perfil siempre se crea como cliente, ignorando roles enviados durante el registro. El navegador puede leer su propio perfil y modificar nombre/teléfono; las operaciones administrativas y de mensajería pasan por FastAPI.

## 9. Probar la conexión de autenticación

Con sesión iniciada en http://127.0.0.1:5173, abre la consola de las herramientas de desarrollo del navegador y ejecuta:

```javascript
const { supabase } = await import('/src/services/supabaseClient.js');
const { data, error } = await supabase.auth.getSession();
if (error) throw error;
if (!data.session) throw new Error('Primero inicia sesión');
const respuesta = await fetch('http://127.0.0.1:8000/api/v1/auth/me', {
  headers: { Authorization: `Bearer ${data.session.access_token}` }
});
console.log(respuesta.status, await respuesta.json());
```

Este ejemplo es para Vite en desarrollo y no imprime el token. Debe mostrar **200** y tu `id`/`role`: comprueba navegador → Supabase Auth → JWT → FastAPI → perfil de Supabase. `/health` solo comprueba que la API está encendida.

## 10. Diagnóstico y límites

| Síntoma | Revisar |
|---|---|
| Falla el registro o falta `profiles` | SQL completo y logs del trigger en Supabase |
| `Email not confirmed` | Confirmar correo antes de iniciar sesión |
| `401 Token inválido o expirado` | Mismo proyecto en ambos `.env`, issuer correcto, algoritmo asimétrico; cerrar sesión y volver a entrar |
| `403 Perfil no autorizado` | Fila `profiles` con UUID del usuario y rol permitido |
| `503 No se pudo verificar el perfil` | URL y clave legacy `service_role` correctas; tabla y Data API disponibles |
| `503 Autenticación no configurada` | Completar las cuatro variables Supabase del backend y reiniciar |
| Error CORS | Dirección exacta del frontend en `ALLOWED_ORIGINS` |
| Siguen apareciendo botones demo | Reiniciar Vite y revisar sus dos variables Supabase |
| El catálogo está vacío | Revisa `products` en Supabase y registra productos reales desde Administración; no se copian los ejemplos automáticamente |

Corrección local de CORS: el archivo `backend/.env` sobrescribe los valores predeterminados del código. Debe incluir `http://127.0.0.1:5173` si se navega con esa dirección. Se unificó `VITE_API_BASE_URL` en `http://127.0.0.1:8000/api/v1` y se reiniciaron ambos servidores. Comprobadas solicitudes OPTIONS y GET de productos/categorías con respuesta 200 y `Access-Control-Allow-Origin` correcto. Después de cambiar estas variables, reiniciar ambos servidores y recargar el navegador.

Esta entrega prepara la base y la conexión de **autenticación/perfiles**. Productos, categorías de la API, contenido institucional, carritos, pedidos, inventario, cotizaciones, entregas y pagos todavía necesitan repositorios reales en FastAPI. El script no implementa creación atómica de pedidos, descuento de inventario ni webhooks de pago. Los servicios actuales no deben utilizarse para compras/pagos reales.

Las futuras operaciones con `service_role` deben validar roles, asignaciones, precios y stock en backend: esa clave elude RLS. El navegador no puede escribir directamente en tablas comerciales. Tampoco puede cargar/borrar archivos: usa el Dashboard o un futuro endpoint autorizado. Las evidencias privadas deberán entregarse solo a usuarios autorizados mediante backend.

Al configurar Supabase, frontend y backend propagan errores sin simular guardados. La versión actual integra los repositorios comerciales; requiere las tablas y funciones de la migración 0005. El modo de memoria solo se utiliza cuando no hay configuración de Supabase.

Verificación local: ambos SQL pasan el análisis de sintaxis PostgreSQL con pglast; 10 pruebas de backend y 5 de frontend aprobadas, y compilación frontend correcta. El SQL no se ha aplicado a tu proyecto remoto. Usa el archivo de verificación después de instalarlo; el análisis de sintaxis no comprueba los permisos ni la ejecución en Supabase.

Referencias: https://supabase.com/docs/guides/auth/managing-user-data y https://supabase.com/docs/guides/database/postgres/row-level-security
# Si `/auth/me` responde 401

El frontend intenta renovar la sesión de Supabase una sola vez y repite la solicitud con el nuevo token. Si la renovación falla, vuelve a iniciar sesión. No es necesario cambiar la contraseña ni volver a ejecutar el SQL por este error.

El backend admite 30 segundos de diferencia entre relojes, manteniendo la validación de firma, emisor y audiencia. En Windows, activa **Configuración → Hora e idioma → Fecha y hora → Establecer hora automáticamente** y pulsa **Sincronizar ahora** si el problema continúa.

Para diagnosticar un rechazo persistente, revisa en **Red → auth/me → Encabezados de respuesta** el valor de `X-Auth-Error`: `token_expired` indica caducidad, `token_not_yet_valid` indica una diferencia de reloj superior a la tolerancia y `token_invalid` indica otro rechazo de validación. Comparte únicamente ese código; no compartas tokens ni el encabezado Authorization. Reinicia el backend con `./iniciar-backend.ps1` después de cambiar su configuración.


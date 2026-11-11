# Neifit: preparación y despliegue

> **Esquema físico en español:** para una instalación vacía utiliza únicamente
> `supabase/neifit_esquema_completo_espanol.sql`. No ejecutes después
> `activar_servicios_supabase.sql` ni la migración 0009. La alerta “Falta aplicar una
> migración” también puede indicar que Render conserva una versión anterior del backend;
> vuelve a desplegar el commit que consulta `perfiles`, `productos`, `pedidos`,
> `configuracion_empresa` y las RPC `neifit_*` en español.

Estado: código preparado para un piloto; **todavía no publicado ni aprobado para compradores**. No necesitas comprar un dominio: utiliza las URL HTTPS asignadas por Vercel y Render.

## Cambios de esta etapa

- Mi cuenta guarda nombre/teléfono y permite crear, editar y eliminar direcciones propias. Checkout permite seleccionarlas; no cambia pedidos históricos.
- Cotizaciones: el administrador guarda un total final (domicilio e impuestos aplicables incluidos), condiciones y vigencia. El cliente consulta la oferta en Mis cotizaciones. El enlace de WhatsApp sigue siendo una acción manual, no un envío automático.
- Avisos internos: pedidos, cotizaciones, ofertas y cambios de estado/pago generan avisos transaccionales para dueño y personal con permiso de gestión. La campana consulta los 50 recientes cada 30 segundos con la pestaña visible. No envía correos, WhatsApp ni notificaciones cuando la aplicación está cerrada.
- Contraentrega: solo administrador, solo pedido entregado, importe exacto y confirmación explícita del dinero recibido. Registra recibo, actor y auditoría; reintentos no duplican el cobro. Transferencias y pasarelas no tienen confirmación automática.
- La landing obtiene textos, valores, contacto, dirección y horarios de Supabase.
- Administración → Contenido institucional permite editar esos datos. Los pagos con proveedor interno `simulacion_consultas` quedan excluidos del indicador de ingresos; esto no sustituye retirar los escenarios inventados antes de vender.
- Logs operativos JSON con identificador de solicitud, ruta de plantilla, estado y duración; no registran tokens ni cuerpos. `/ready` comprueba acceso a las tablas nuevas. `/health` comprueba que el proceso responde.
- `production` rechaza DEBUG, autenticación demo, RBAC desactivado, Supabase incompleto y CORS sin HTTPS. Documentación interactiva desactivada en producción.
- Cabeceras para claves nuevas `sb_secret_` y legacy; la clave nueva no se envía como JWT.

## 1. Supabase existente

Haz un respaldo previo. En SQL Editor ejecuta TODO `supabase/activar_servicios_supabase.sql`. Incluye 0003/0004 si faltan y actualiza 0005/0006/0007 sin borrar registros. Si ya aplicaste hasta 0005, basta ejecutar 0006 y 0007 completos en ese orden. **No ejecutar el instalador de base nueva sobre tu base existente.**

Para tu base actual, `supabase/preparar_piloto_produccion.sql` reúne 0006 y 0007 en una transacción y verifica el requisito 0005. Es el mismo bloque entregado por el chat.

Verifica:

```sql
select tablename, rowsecurity from pg_tables
where schemaname='public' and tablename in ('customer_addresses','notifications');
select column_name from information_schema.columns
where table_schema='public' and table_name='quotes'
and column_name in ('offered_total','offer_conditions','offer_valid_until');
```

Antes de publicar: crea una clave secreta nueva en Supabase, colócala únicamente en Render y en backend/.env, comprueba el acceso y revoca la clave expuesta anterior. Crear una clave nueva por sí solo no revoca la anterior. No la pegues en chats, Vercel ni GitHub. Documentación: https://supabase.com/docs/guides/security/rotate-leaked-api-keys y https://supabase.com/docs/guides/getting-started/api-keys

## 2. Subir código revisado a GitHub

Comprueba que `.env`, backups y contraseñas no estén en el commit. `.gitignore` los excluye. Conserva el proyecto Supabase existente para la demostración, pero antes de vender decide cómo retirar los productos/pedidos/cotizaciones inventados: el manifiesto `supabase/datos_consulta_creados.json` identifica esos registros. Dos pagos fueron SIMULADOS y no representan dinero recibido; no usar sus ingresos para contabilidad. Esta etapa no borra esos registros ni cambia sus importes.

El despliegue necesita que los nuevos archivos y requirements/package-lock estén en el repositorio conectado. No basta con modificar archivos locales. No se realizó commit/push ni publicación desde esta sesión.

## 3. Frontend en Vercel

1. Importa el repositorio de GitHub como proyecto Vercel.
2. Root Directory: `frontend`. Framework: Vite. Install: `npm ci`. Build: `npm run build`. Output: `dist`. Node: 22.x.
3. Define variables (Production):
   - `VITE_SUPABASE_URL`: URL pública de tu proyecto.
   - `VITE_SUPABASE_PUBLISHABLE_KEY`: clave pública `sb_publishable_...`.
   - `VITE_API_BASE_URL`: `https://TU-SERVICIO.onrender.com/api/v1` (actualizar cuando Render asigne la URL).
4. Copia la URL estable de producción, por ejemplo `https://TU-PROYECTO.vercel.app`. No uses una URL distinta de preview en CORS/Auth.
5. `frontend/vercel.json` permite recargar rutas como `/mi-cuenta` sin 404. Las variables VITE se incorporan durante build: haz Redeploy después de cambiarlas.

## 4. Backend en Render

1. New → Web Service → conecta el mismo repositorio. Root Directory: `backend`. Runtime Python 3; Python 3.12.12.
2. Build: `pip install -r requirements.txt`.
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`.
4. Health check: `/ready`. También se incluye `render.yaml` para crear un Blueprint; no duplica ni crea bases de datos.
5. Variables de Render (valores privados solo en el panel):

```dotenv
APP_ENV=production
DEBUG=false
ENABLE_DEMO_AUTH=false
RBAC_DATABASE_ENABLED=true
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_JWT_ISSUER=https://TU-PROYECTO.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://TU-PROYECTO.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=CLAVE_SECRETA_NUEVA_SOLO_SERVIDOR
ALLOWED_ORIGINS=["https://TU-PROYECTO.vercel.app"]
```

`DATABASE_URL` no es necesaria para el backend REST; sí se necesita una conexión PostgreSQL directa/pooler adecuada para `pg_dump`. No copies la URL `/rest/v1/` en DATABASE_URL. No reutilices SECRET_KEY de desarrollo para otros servicios.

6. Despliega Render, comprueba `/health` y `/ready` (200), copia su URL a Vercel y vuelve a desplegar frontend.
7. El Blueprint usa plan free para evitar contratación automática. Revisa disponibilidad, suspensión por inactividad y límites del plan antes de recibir compradores; no se certifica continuidad comercial con ese plan.

Fuentes oficiales: https://render.com/docs/deploy-fastapi, https://render.com/docs/blueprint-spec y https://vercel.com/docs/frameworks/frontend/vite

## 5. Auth y recuperación

Supabase → Authentication → URL Configuration:
- Site URL: URL de producción de Vercel.
- Redirect URLs: `https://TU-PROYECTO.vercel.app/auth/callback` y `https://TU-PROYECTO.vercel.app/restablecer-contrasena`.
- Conserva localhost solo para desarrollo si todavía lo necesitas.

Google: conserva como callback OAuth de Google la URL de Supabase `/auth/v1/callback`; revisa los orígenes permitidos y el estado de publicación/usuarios de prueba de tu aplicación Google. Configura SMTP y remitente verificado para recuperar contraseña. Prueba con un correo real después del despliegue; no se ha verificado entrega de correos en esta sesión.

## 6. Información y datos que requieren confirmación del negocio

No presentar como aprobados los textos provisionales de `/terminos` y `/politica-privacidad`. Falta confirmar zonas/barrios atendidos, costo real del domicilio, tiempos, horarios de entrega, responsables de atención, cancelación/reembolso, tratamiento de datos, conservación y canal de solicitudes. Falta validar catálogo, precios, existencias, ingredientes, alérgenos y fotografías con el negocio. No se inventan estas decisiones.

## 7. Registro, alertas y recuperación

- Render → Logs: busca `request_id` compartido por soporte y eventos con estado >=500. No habilites logging de cuerpos ni cabeceras Authorization.
- Configura en tu cuenta de alojamiento/monitorización un aviso de caída para `/ready` y destinatario real. No hay alertas externas ni destinatario configurados desde esta sesión.
- Antes de migrar, respalda con `pg_dump --format=custom --file backups/neifit_FECHA.dump` usando un servicio PostgreSQL (`PGSERVICE`) o credenciales en variables de entorno/archivo pgpass protegido; nunca una contraseña en el comando compartido. Usa versión de pg_dump compatible con el servidor.
- Guarda copia cifrada fuera del equipo, acceso restringido, responsable y frecuencia diaria. Auth y Storage tienen componentes propios: los archivos de Storage no están incluidos en un dump SQL. Incluye objetos de Storage y configuración Auth/SMTP/OAuth en el procedimiento de recuperación con acceso restringido.
- Restaura primero en un entorno vacío y aislado con `pg_restore --exit-on-error --dbname BASE_AISLADA backups/neifit_FECHA.dump`. No usar `--clean` contra producción. En Supabase respeta sus esquemas administrados y procedimiento oficial de backups, no restaures un dump completo a ciegas.
- Ensayo automatizado LOCAL: `uv run --no-project --with playwright --with "psycopg[binary]" --python backend/.venv/Scripts/python.exe python backend/tests/run_commerce_checks.py --browser`. Restaura pedidos, perfiles, avisos y cobros y comprueba RLS/privilegios. Esto no sustituye un ensayo del respaldo del Supabase real.
- Si falla despliegue, vuelve a la versión anterior en ambos proveedores; conserva migraciones aditivas y revisa compatibilidad. No reviertas borrando tablas.

## 8. Prueba de aceptación antes de abrir ventas

Con usuarios separados y datos confirmados: registro/Google, recuperación por correo real, edición de perfil, direcciones, cotización/oferta/aviso, pedido contraentrega, descuento de stock, visibilidad administrador, asignación mensajero, entrega, registro manual del cobro y consulta del cliente. Verificar que otro cliente no pueda leer esos registros, ni un mensajero cobrar/administrar roles. Comprueba móvil, recarga de rutas y copia/restauración. Solo entonces habilitar ventas del piloto.

# Replicar la base de datos de Neifit

Este paquete permite instalar el modelo completo en un proyecto **nuevo de Supabase**. Incluye tablas, relaciones, índices, restricciones, funciones, triggers, RLS, roles y permisos de aplicación, y la definición de los buckets de Storage.

No es un respaldo de los datos de Maribel. No copia cuentas de Auth, contraseñas, pedidos, cotizaciones, pagos, secretos ni archivos de Storage. Las categorías y textos institucionales iniciales sí se incluyen; revisa los datos comerciales si vas a adaptarlos a otra empresa.

## 1. Crear el proyecto

1. Ingresa en https://supabase.com/dashboard con tu propia cuenta.
2. Crea un proyecto nuevo dentro de tu organización.
3. Asigna nombre y una contraseña de base de datos propia; guárdala de forma privada.
4. Espera a que el proyecto termine de aprovisionarse.

Supabase proporciona PostgreSQL, los roles de plataforma y los esquemas `auth` y `storage`. Este script depende de ellos: no se ejecuta directamente en MySQL, SQL Server o un PostgreSQL sin Supabase.

## 2. Instalar el SQL completo

1. Abre **SQL Editor → New query**.
2. Abre **neifit_completo_base_nueva.sql** en un editor de texto.
3. Copia TODO el contenido y pégalo en SQL Editor.
4. Ejecuta con el usuario propietario de la base, normalmente `postgres`.
5. Al terminar deben aparecer **21 tablas**, todas con `rowsecurity = true`.

El archivo combina `neifit_inicial.sql` y las migraciones 0002 a 0007 en una sola transacción. **No ejecutes esos archivos otra vez después de instalar este.** No incluye instrucciones DROP TABLE ni un reinicio del esquema. Si detecta tablas de Neifit existentes, se detiene para evitar mezclar instalaciones.

Si aparece un error, no continúes con las variables del backend hasta resolverlo. Si SQL Editor mantiene la transacción fallida en la misma sesión, ejecuta `rollback;` antes de reintentar el instalador corregido.

## 3. Verificar

Ejecuta **verificar_replicacion.sql** completo. Debe finalizar sin excepciones y mostrar `true` en las comprobaciones de privilegios. Los datos iniciales esperados son:

- 21 tablas con RLS.
- 3 categorías: Postres, Snacks y Bebidas.
- 5 contenidos institucionales y 6 valores de empresa.
- 3 roles base: admin, cliente y mensajeria.
- 16 permisos para admin, 6 para cliente y 5 para mensajeria.
- Tablas comerciales vacías hasta registrar información real.

Si ya había cuentas registradas en el nuevo proyecto, el instalador crea sus perfiles con rol cliente. No copia cuentas desde otro proyecto.

## 4. Conectar una copia de la aplicación

Cada compañero debe usar las credenciales de SU proyecto, no las del proyecto original. Copia los `.env.example` del repositorio a sus respectivos `.env` y completa los valores localmente.

En `frontend/.env`:

```dotenv
VITE_SUPABASE_URL=https://TU_REFERENCIA.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=TU_CLAVE_PUBLICABLE
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

En `backend/.env`:

```dotenv
SUPABASE_URL=https://TU_REFERENCIA.supabase.co
SUPABASE_JWT_ISSUER=https://TU_REFERENCIA.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://TU_REFERENCIA.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=TU_CLAVE_DE_SERVIDOR
RBAC_DATABASE_ENABLED=true
ENABLE_DEMO_AUTH=false
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=["http://127.0.0.1:5173","http://localhost:5173"]
```

Los marcadores no son credenciales válidas. Obtén la clave pública y la de servidor desde la configuración de tu proyecto. Nunca pongas la clave de servidor en variables `VITE_*`, en el chat o en el repositorio. `DATABASE_URL` queda reservado a una conexión PostgreSQL directa si una tarea la requiere; no se rellena con la URL REST.

Reinicia frontend y backend después de configurar sus archivos. Para autenticación, el backend actual verifica JWT firmados con RS256 o ES256 mediante JWKS; si el proyecto utiliza una clave heredada HS256, revisa su configuración de firma antes de probar el acceso.

## 5. Crear el primer administrador

1. Registra una cuenta propia desde la aplicación o desde Authentication en Supabase.
2. Si la confirmación de correo está activa, completa la confirmación antes de entrar.
3. En SQL Editor, identifica su perfil:

```sql
select id, full_name, email, role
from public.profiles
order by created_at desc;
```

4. Como propietario del proyecto, sustituye la UUID y ejecuta:

```sql
update public.profiles
set role = 'admin'
where id = 'UUID_DE_TU_CUENTA'::uuid
returning id, email, role;
```

5. Debe devolver exactamente la cuenta elegida. Recarga la aplicación o inicia sesión nuevamente. Los siguientes cambios de usuarios y roles se gestionan desde el panel autorizado.

No se crean administradores ni contraseñas predeterminadas en el instalador.

## 6. Configuración adicional

- **Google:** activa el proveedor en este nuevo proyecto y usa su propio callback `https://TU_REFERENCIA.supabase.co/auth/v1/callback`. Configura el cliente OAuth correspondiente en Google Cloud.
- **URL de retorno:** autoriza las rutas locales `/auth/callback` y `/restablecer-contrasena` para los orígenes que utilices, siguiendo las guías del repositorio.
- **Correo:** configura el envío y las plantillas si vas a probar recuperación o confirmación de cuentas.
- **Storage:** se crean los buckets `products` y `evidence`, pero no se copian imágenes ni evidencias. El navegador no recibe permisos de carga/borrado por defecto.
- **Productos:** no se insertan productos, precios o stock ficticios. Los identificadores de las categorías se generan en cada instalación.

## Alcance real

El script replica el **modelo completo y las funciones comerciales**. La versión actual del backend utiliza Supabase para productos, pedidos, cotizaciones y seguimiento cuando tiene sus variables configuradas. No se copian los registros del antiguo modo de memoria. Sigue `PERSISTENCIA_SUPABASE.md` del repositorio para activar, cargar productos reales y verificar la operación. El carrito continúa local y los pagos reales requieren una integración adicional con el proveedor.

El archivo ha sido revisado mediante análisis sintáctico SQL/PLpgSQL. La comprobación definitiva es ejecutar el instalador y la verificación en el proyecto nuevo del compañero.

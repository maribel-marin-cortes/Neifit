# Roles y permisos de Neifit

## Usuarios y roles personalizados

El administrador tiene un módulo **Usuarios** (`/usuarios`, permiso `users.manage`) para registrar nombre, correo, teléfono, contraseña inicial y rol. El rol inicial del formulario es Mensajero / domiciliario. También permite asignar un rol distinto a una cuenta existente. El registro público continúa creando exclusivamente clientes.

En **Roles y permisos** (`/admin?modulo=accesos`, permiso `access.manage`) puede crear roles con nombre, código y permisos, y modificar sus permisos posteriormente. Los códigos aparecen bajo el nombre de cada permiso y de cada enlace del menú. Los roles personalizados acceden a las vistas según sus permisos; no necesitan llamarse admin o mensajeria. El permiso `profile.read` es obligatorio. Los permisos `users.manage` y `access.manage` están reservados al administrador; no son delegables.

### Activación de esta ampliación

La comprobación de Supabase en esta implementación devolvió tablas `permissions` y `access_roles` ausentes. No se han aplicado migraciones remotas. La clave de servicio permite gestionar Auth y la Data API, pero no sustituye una conexión PostgreSQL para ejecutar migraciones.

1. Abre el **SQL Editor** de tu proyecto Supabase, con el esquema inicial ya instalado.
2. Si todavía no instalaste la gestión de roles, ejecuta **supabase/instalar_usuarios_roles.sql** completo una sola vez. Incluye las migraciones 0002, 0003 y 0004 en una sola transacción. No ejecutes además esas migraciones individualmente.
3. Si ya aplicaste 0003 anteriormente, ejecuta solamente **supabase/migrations/0004_usuarios_roles_personalizados.sql**. No vuelvas a ejecutar el instalador completo.
4. Ejecuta **supabase/verificar_usuarios_roles.sql**. Debe mostrar las comprobaciones en true y los tres roles iniciales.
5. En `backend/.env`, establece `RBAC_DATABASE_ENABLED=true`. Conserva los demás valores.
6. Reinicia el backend con `.\iniciar-backend.ps1` y recarga el navegador.
7. Ingresa como administrador. En Usuarios registra el mensajero. En Roles y permisos crea los roles adicionales que necesites y después asígnalos desde Usuarios.

No actives la variable antes de terminar el SQL: el backend rechaza consultas si no puede comprobar los permisos.

### Registro administrativo

El administrador debe verificar que el correo pertenece a la persona y marcar la casilla del formulario. Esta alta crea una cuenta con correo confirmado, sin enviar correos automáticos. La contraseña se comunica directamente a su titular y no se guarda en profiles ni se devuelve en la respuesta. Para cambiarla puede utilizar la recuperación de contraseña ya existente. No se inicia sesión como el mensajero ni se reemplaza la sesión del administrador.

El servidor crea inicialmente la identidad bloqueada, asigna el rol mediante la función auditada y habilita el acceso al terminar. Si falla la asignación o activación, intenta eliminar exclusivamente la identidad que acaba de crear. Si no puede completar esa limpieza, muestra un error para revisar Authentication → Users antes de reintentar. La creación en Auth y el cambio de rol en PostgreSQL son operaciones separadas; ante un corte de red puede requerirse esa revisión.

### Permisos por vista

| Vista | Permiso |
|---|---|
| Catálogo y detalle | `catalog.read` |
| Carrito y compra | `orders.create` |
| Mis pedidos y seguimiento propio | `orders.read_own` |
| Cotizador | `quotes.create` |
| Perfil | `profile.read` |
| Mensajería: pedidos asignados | `delivery.read_assigned` |
| Despachar/iniciar recorrido | `delivery.start` |
| Confirmar entrega | `delivery.complete` |
| Registrar novedad | `delivery.issue` |
| Productos e inventario | `products.manage` |
| Resumen y gestión de pedidos | `orders.manage` |
| Gestión de cotizaciones | `quotes.manage` |
| Usuarios | `users.manage` (administrador) |
| Roles y permisos | `access.manage` (administrador) |

`quotes.read_own` autoriza la consulta API de cotizaciones propias; `content.manage` autoriza las operaciones existentes de contenido en la API. No se crean pantallas adicionales para esos dos permisos en esta ampliación. Las vistas públicas institucionales no requieren permiso.

La asignación de permisos regula también las operaciones; no solo oculta enlaces. Mensajería conserva el acceso únicamente a pedidos asignados. Un rol que combine compras y entregas solo ve importes completos en sus propios pedidos o cuando tenga `orders.manage`.

Verificación de esta ampliación: 38 pruebas backend y 35 frontend, compilación y análisis SQL/PLpgSQL. Las pruebas de altas usan servicios simulados: no registran personas ni envían correos reales. La migración y un alta real siguen pendientes de ejecutarse en tu instancia.

## Modelo implementado

Se mantienen como roles base `cliente`, `mensajeria` (mensajero/domiciliario) y `admin`, y se admiten roles personalizados tras aplicar 0004. Los permisos se asignan al rol, no individualmente a una persona. Cada cuenta tiene un rol en `profiles`; ese rol se consulta en servidor, nunca desde metadatos editables por el usuario.

| Rol | Permisos base |
|---|---|
| Cliente | Catálogo, crear pedidos, consultar pedidos propios, crear/consultar cotizaciones propias y perfil propio |
| Mensajería | Consultar entregas asignadas, despachar/iniciar recorrido, registrar novedad, confirmar entrega y perfil propio |
| Administrador | Gestión completa de productos, pedidos, cotizaciones, contenido y accesos |

El administrador puede activar o desactivar los permisos delegables de cliente/mensajería, dentro de esos límites. No se puede conceder gestión de productos, usuarios o pagos al mensajero. El permiso de perfil propio es obligatorio. El administrador conserva su conjunto completo para evitar perder la administración.

## Activar gestión persistente en Supabase

1. Si ya creaste el esquema, no vuelvas a ejecutar `neifit_inicial.sql`.
2. Ejecuta `supabase/migrations/0002_catalogo_autenticado.sql` si aún no lo aplicaste.
3. Ejecuta TODO `supabase/migrations/0003_roles_permisos.sql` en **SQL Editor** una sola vez. Crea catálogo de permisos, límites por rol, asignaciones y auditoría; añade las funciones de gestión y actualiza RLS. La consulta final debe mostrar 15 permisos de administrador, 6 de cliente y 5 de mensajería antes de cualquier cambio.
4. Ejecuta `supabase/verificar_roles.sql` para comprobar privilegios de tablas y funciones.
5. En `backend/.env`, agrega:

```dotenv
RBAC_DATABASE_ENABLED=true
```

6. Reinicia el backend desde la raíz:

```powershell
.\iniciar-backend.ps1
```

7. Entra con una cuenta administradora y recarga la aplicación. Abre **Menú → Administración → Roles y permisos**.

Antes de completar esos pasos, el backend utiliza los permisos base y el panel muestra la configuración sin permitir guardarla. No simula cambios persistentes. Después de activar la variable, una caída/error de lectura de permisos devuelve un error de servicio; no se sustituye silenciosamente por permisos base que pudieran haber sido revocados.

La migración no se ha aplicado remotamente desde esta sesión. El análisis local de sintaxis SQL no sustituye a ejecutarla y comprobar RLS en tu instancia.

## Primer administrador

Si aún no existe, el propietario del proyecto Supabase puede consultar `profiles` en SQL Editor, identificar la UUID de la cuenta autorizada y ejecutar una sola vez:

```sql
update public.profiles
set role = 'admin'
where id = 'UUID_DE_LA_CUENTA_AUTORIZADA'::uuid
returning id, email, role;
```

Esto es un procedimiento inicial del propietario con privilegios de base de datos. Desde la aplicación ningún usuario, incluido un administrador, puede cambiar su propio rol. No compartas acceso al SQL Editor con clientes o mensajeros.

## Uso del panel

1. En el bloque de Cliente o Mensajero/domiciliario, marca los permisos que quieres habilitar y pulsa **Guardar permisos**.
2. Para modificar una cuenta, localízala por nombre/correo en **Asignar rol a usuarios** y selecciona su rol. El cambio se guarda en Supabase; el panel muestra el resultado o un error.
3. Se muestran hasta 100 cuentas recientes. No es todavía un buscador global paginado.
4. El cambio de permisos afecta a TODAS las cuentas del rol. El backend vuelve a consultarlos en cada petición. El usuario puede recargar o volver a la pestaña para actualizar el menú; una vista antigua no autoriza operaciones en la API.
5. Para usar acciones de entrega, mantén activo **Consultar entregas asignadas**. Sin ese permiso la API no permite operar sobre el pedido aunque se haya marcado una acción individual.

La interfaz no permite cambiar el rol propio, exceder los permisos delegables ni editar los permisos completos del administrador. Las funciones PostgreSQL vuelven a validar estas restricciones, serializan cambios de acceso y verifican que el actor siga siendo administrador dentro de la transacción.

## Restricciones del mensajero

- Solo consulta y modifica pedidos asignados a su identificador.
- No recibe importes, precios unitarios, correo del cliente ni datos de pago en las respuestas logísticas.
- Puede marcar despachado desde empacado, en ruta desde despachado y entregado desde en ruta, si tiene el permiso de la acción.
- Puede registrar novedad desde empacado, despachado o en ruta.
- No cancela pedidos ni cambia estados de preparación. No modifica pedidos entregados/cancelados mediante acciones logísticas.
- Los cambios de estado siguen bloqueados aunque se envíe la petición manualmente desde fuera de la interfaz.

## Seguridad de base de datos y auditoría

`role_permissions`, `role_permission_limits`, `permissions` y `access_audit` tienen RLS. Los usuarios pueden consultar sus propios permisos, pero no modificarlos. Las funciones de cambios solo se conceden a `service_role`; FastAPI establece el actor usando la identidad autenticada. No se acepta un actor enviado por el cliente.

`neifit_has_permission` refuerza RLS en productos, carrito, pedidos, cotizaciones y trazabilidad. Mensajería no obtiene acceso directo a pedidos completos mediante la Data API: utiliza la API con proyección logística. El servidor con `service_role` debe seguir comprobando permisos/asignación porque dicha clave elude RLS.

Cada cambio persistente de rol/permisos registra actor, fecha, objetivo y detalle en `access_audit`, consultable por el propietario desde SQL Editor. El acceso directo autenticado/anónimo a esa tabla queda bloqueado. La aplicación no incluye todavía una pantalla de consulta de auditoría.

## Verificaciones y alcance

Se comprobaron 32 pruebas frontend, 23 backend, compilación y navegador con sesiones/respuestas simuladas: acceso al editor, guardado de permisos, asignación de rol, bloqueo del rol propio, bloqueo de rutas administrativas y ocultación de la acción de entrega revocada. Se verifican además permisos retirados, aislamiento de pedidos, proyección logística y transiciones prohibidas.

La gestión de roles/permisos usa persistencia real mediante RPC cuando está activada. La ampliación comercial actual también implementa pedidos, cotizaciones e inventario persistentes mediante la migración 0005. Sigue **PERSISTENCIA_SUPABASE.md**; el archivo `supabase/activar_servicios_supabase.sql` reúne la actualización sobre una base existente. La aplicación de SQL y la verificación en el proyecto remoto siguen siendo necesarias. Los pagos reales requieren integrar y verificar el proveedor.

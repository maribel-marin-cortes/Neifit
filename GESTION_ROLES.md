# Roles y permisos de Neifit

## Modelo implementado

Se mantienen los roles `cliente`, `mensajeria` (mensajero/domiciliario) y `admin`. Los permisos se asignan al rol, no individualmente a una persona. Cada cuenta tiene un rol en `profiles`; ese rol se consulta en servidor, nunca desde metadatos editables por el usuario.

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

La gestión de roles/permisos usa persistencia real mediante RPC cuando está activada. Los servicios comerciales de pedidos y cotizaciones continúan en memoria de demostración: este cambio añade autorización y propiedad, no implementa sus repositorios transaccionales reales ni pagos. Las políticas y RPC SQL requieren su verificación en Supabase después de la instalación.

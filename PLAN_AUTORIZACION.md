# Acceso público, clientes y personal de Neifit

## Gestión de roles y permisos implementada

La autorización ahora utiliza permisos específicos por rol además de propiedad/asignación. El panel **Administración → Roles y permisos** permite configurar los permisos delegables de cliente y mensajería y asignar roles a cuentas. Activación, migración y límites en `GESTION_ROLES.md`. El estado de aprobación manual de clientes sigue sin implementarse; asignar un rol no equivale a un flujo de aprobación comercial.

## Distribución implementada

| Acceso | Visitante | Cliente con sesión | Mensajería | Administrador |
|---|---|---|---|---|
| Landing, empresa, misión, valores y contacto | Sí | Sí | Sí | Sí |
| Muestra pública de tres productos | Sí | Sí | Sí | Sí |
| Login, registro y recuperación independientes | Sí | Sí | Sí | Sí |
| Catálogo completo, detalle, carrito y cotizador en la web | Redirige a login | Sí | No | Sí |
| Mis pedidos y seguimiento desde la web | Redirige a login | Sus pedidos | Mediante panel de entregas | Sí |
| Perfil | Redirige a login | Propio | Propio | Propio |
| Administración | No | No | No | Sí |
| Mensajería | No | No | Asignados | Sí |

Para visitantes, el encabezado muestra información de marca, contacto, Ingresar y Crear cuenta. No muestra sidebar, módulos ni carrito. El footer utiliza enlaces institucionales. Las páginas de login, registro, recuperación y retorno Google no incluyen encabezado, sidebar ni footer de los módulos.

## Recorrido del cliente

1. El visitante abre `/` y conoce la empresa; solo se muestra una selección pública de productos.
2. Al seleccionar un producto o intentar entrar a un módulo privado se abre `/login?next=...`.
3. Puede acceder mediante correo/contraseña o Google, o utilizar el formulario de creación de cuenta. El registro también tiene ruta directa `/registro`.
4. Si Supabase exige confirmación de correo, debe completar esa confirmación antes de entrar. El mensaje se mantiene en login.
5. Al iniciar sesión se recupera el destino interno solicitado. Los destinos externos y las rutas que provocarían bucles de login se descartan. Google conserva el destino en la URL del callback.
6. El cliente ve los módulos de compras y su propia cuenta. Administrador y mensajería conservan sus permisos específicos. No se permite que un cliente se asigne roles.

El alta normal autoriza como cliente una vez que Supabase valida la cuenta y su sesión. **No existe todavía aprobación manual del cliente por parte del administrador**. Si se decide exigirla, hará falta un estado de aprobación en profiles, su gestión administrativa, comprobación en cada endpoint protegido y políticas RLS correspondientes; no debe simularse ocultando enlaces.

## Protección del backend

- `/api/v1/products/`, el detalle del producto, `/categories/` y `/tracking/{codigo}` requieren autenticación.
- El seguimiento comprueba propiedad del pedido, rol administrador o asignación al mensajero. Un código de pedido por sí solo no autoriza a leer datos.
- La landing consulta `/api/v1/site/featured-products`: un máximo de tres productos y un esquema limitado sin cantidades de inventario.
- `/api/v1/site/categories` publica únicamente categorías de presentación. El contenido institucional continúa siendo público.
- Las escrituras y módulos existentes conservan las verificaciones de roles en la API.

## Paso pendiente en Supabase ya instalado

Ejecuta en SQL Editor **solo** el archivo:

```text
supabase/migrations/0002_catalogo_autenticado.sql
```

Este cambio retira el permiso directo de lectura de `products` para `anon`, sin borrar datos ni modificar el acceso a contenido institucional. La consulta final debe devolver `anon_puede_leer_catalogo = false`. No vuelvas a ejecutar `neifit_inicial.sql` sobre la base existente.

La migración está preparada pero no se ha aplicado remotamente desde esta sesión. Hasta ejecutarla, las políticas antiguas de Supabase pueden seguir permitiendo lectura directa anónima de `products` mediante la Data API, aunque la web y la API FastAPI ya exijan sesión. Las instalaciones nuevas usan el esquema inicial actualizado.

## Validación y alcance

Pruebas locales: 31 pruebas frontend, 13 de backend y compilación correctas. Se verifica el acceso anónimo a la muestra pública, rechazo de catálogo/detalle/seguimiento sin sesión y aislamiento del seguimiento entre clientes.

Los servicios comerciales siguen utilizando memoria de demostración; este cambio aplica control de acceso, no implementa su persistencia real en Supabase. La habilitación de Google, correo transaccional y confirmación de cuentas permanece sujeta a la configuración real del panel.

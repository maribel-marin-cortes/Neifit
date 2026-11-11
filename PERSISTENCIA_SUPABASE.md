# Conectar y utilizar los servicios comerciales de Neifit

> **Instalación nueva con tablas físicas en español:** ejecuta solamente
> `supabase/neifit_esquema_completo_espanol.sql`. Las instrucciones de
> `activar_servicios_supabase.sql` que aparecen debajo corresponden exclusivamente al
> esquema histórico en inglés y no deben aplicarse sobre la instalación española.

Para comprobar la instalación española:

```sql
select tablename, rowsecurity
from pg_tables
where schemaname = 'public'
order by tablename;

select public.neifit_leer_pedidos(
  (select id from public.perfiles limit 1), null, null
);
```

Después de cambiar al esquema español es obligatorio volver a desplegar el backend. Una
respuesta `PGRST202`, `PGRST205`, `42P01` o `42703` suele indicar que el backend desplegado
todavía solicita una RPC, tabla o columna del contrato anterior.

El backend ya utiliza la Data API de Supabase cuando tiene `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`. No necesita `DATABASE_URL` para este funcionamiento. Si Supabase falla, no devuelve registros de demostración ni muestra éxito ficticio.

## Activar en el proyecto existente

1. Conserva las variables actuales de Supabase en `backend/.env` y `frontend/.env`. No compartas claves.
2. Abre **supabase/activar_servicios_supabase.sql**, copia TODO y ejecútalo en **Supabase → SQL Editor → Run** como propietario (`postgres`). Conserva los registros y permisos existentes. Instala 0003/0004 únicamente si faltan sus tablas, y aplica 0005, 0006 y 0007. Es una actualización, no el instalador de una base vacía. Para despliegue en Vercel y Render consulta **PRODUCCION.md**.
3. Desde la raíz del proyecto, ejecuta:

   ```powershell
   .\backend\.venv\Scripts\python.exe backend/scripts/verificar_servicios.py --activar
   ```

   El comando comprueba tablas, función de lectura y tarifa de domicilio. Solo si todo pasa escribe `RBAC_DATABASE_ENABLED=true`. Si no pasa, no cambia `.env`.
4. Detén el backend anterior con Ctrl+C y ejecuta `./iniciar-backend.ps1`.
5. Recarga el frontend y vuelve a iniciar sesión si no se actualiza el menú.
6. Ingresa como administrador y abre **Productos e inventario → Nuevo producto**. Selecciona una categoría real y registra nombre, precio y existencias reales. Puedes introducir una URL de imagen o una ruta del frontend, como `/images/postre-maracuya.png`; esas imágenes locales son ilustrativas.
7. Marca **Destacado en inicio** si quieres que aparezca en la muestra pública. Solo se muestran hasta tres destacados activos de categorías activas.
8. Comprueba la creación en SQL Editor:

   ```sql
   select p.id, p.name, c.name as categoria, p.price, p.stock
   from public.products p
   join public.categories c on c.id = p.category_id
   order by p.created_at desc;
   ```

No se insertan automáticamente los precios ni existencias de demostración. Los antiguos carritos con identificadores `prod-1`, `cat-1`, etc., se retiran del frontend: vuelve a seleccionar productos del catálogo real. No es posible recuperar pedidos/cotizaciones que ya se perdieron al reiniciar el antiguo servicio de memoria.

## Aislamiento multiempresa

Desde la migración `0011_multiempresa.sql`, cada solicitud de la API incluye el slug de
la tienda en `X-Empresa` (por defecto `neifit`). El backend resuelve ese slug en
`empresas`; nunca acepta un UUID empresarial proporcionado directamente por el navegador.
Cada tienda puede compartirse inicialmente como `/?empresa=slug-de-la-empresa`; el navegador
conserva la selección y envía el slug en las solicitudes posteriores.
Los usuarios se relacionan mediante `miembros_empresa` y su rol se evalúa dentro de la
empresa activa. Las tablas comerciales guardan `empresa_id`, las relaciones de detalle
usan claves compuestas y las RPC de servidor reciben `p_empresa`.

Para una instalación existente en español ejecuta, en orden, `0010_ajustes_esquema_espanol.sql`
y `0011_multiempresa.sql`. No vuelvas a ejecutar el instalador completo ni elimines tablas.

## Qué se guarda

| Servicio | Tablas / comportamiento |
|---|---|
| Categorías y productos | `categories`, `products`; los productos se desactivan para conservar referencias históricas |
| Cotizaciones | `quotes`, `quote_items`; precios y nombres obtenidos del producto en servidor |
| Pedidos | `orders`, `order_items`; precios, subtotal y domicilio calculados en servidor |
| Inventario | Descuento de stock al crear el pedido; devolución única al cancelar un pedido pendiente permitido |
| Seguimiento | `order_tracking`; estado e historial se actualizan en la misma transacción |
| Mensajería | Asignación persistente a un usuario con `delivery.read_assigned` |
| Institucional | Lectura/escritura en `company_settings`, `site_content`, `company_values` |
| Usuarios y roles | Gestión existente de Auth y RBAC, sin cambiar la sesión del administrador |

El carrito continúa como selección local del navegador; al confirmar se guarda un pedido real. Las tablas de carritos del esquema no se usan para sincronización entre dispositivos en esta ampliación. Los números de documentos generados por PostgreSQL son únicos con prefijo `NF-` o `COT-` y UUID; no se reutiliza un contador en memoria.

## Transacciones y reglas

- `neifit_create_document`: crea la cabecera y los detalles juntos. Los precios, importes y propietario enviados por el navegador no son fuente de verdad.
- Los productos se bloquean por UUID en orden estable. Dos compras no pueden consumir las mismas unidades.
- El costo de domicilio se obtiene de `company_settings.shipping_cost`. La migración conserva la tarifa inicial de 5000 que ya utilizaba el proyecto; el propietario debe revisar que corresponda a su operación.
- La cotización no descuenta stock. Puede registrar interés en cantidades mayores a las disponibles; no promete una reserva.
- La interfaz envía un `request_id` por formulario. Reintentar con el mismo identificador y datos devuelve el mismo documento sin descontar otra vez; si cambia el contenido de una solicitud ya guardada, se rechaza. No es una protección contra crear voluntariamente un formulario nuevo con otro identificador.
- `neifit_update_order` valida permisos, asignación y transición; registra el evento al actualizar. Para despachar se exige mensajero asignado. Entregado y cancelado son terminales.
- La cancelación devuelve stock solo si esta implementación registró el descuento (`stock_debited=true`). No intenta deducir el inventario de pedidos antiguos insertados manualmente.
- Los pedidos pagados requieren revisar reembolso antes de cancelar; no se simula un reembolso.
- Editar existencias requiere `expected_updated_at`; si cambió el producto mientras el formulario estaba abierto, se rechaza para no sobrescribir una venta reciente.
- Las funciones de escritura solo permiten ejecución a `service_role` y vuelven a comprobar al actor en las tablas de permisos. FastAPI obtiene al actor del JWT validado.
- El mensajero recibe solo datos logísticos de los pedidos asignados. Las cuentas de otros clientes no ven el documento, aunque conozcan su número.

## Operación administrativa

**Productos:** crear, editar, activar/desactivar y ajustar existencias. El editor también permite crear una categoría. Cargar una imagen se realiza mediante una URL o ruta existente; no se implementa un cargador de archivos de Storage en este cambio.

**Pedidos:** elegir el mensajero y avanzar los estados. Flujo normal: recibido → confirmado → en_preparacion → empacado → despachado → en_ruta → entregado. Las transiciones inválidas muestran error sin alterar datos. El administrador puede gestionar novedades y cancelaciones en los estados permitidos.

**Cotizaciones:** pendiente → respondida → aceptada/rechazada/cancelada; también se puede rechazar/cancelar una pendiente. Los estados terminales no se reabren. No se envían automáticamente mensajes al cambiar el estado y no se convierte una cotización en pedido sin una solicitud nueva autorizada.

**Contenido:** las operaciones existentes de la API ahora persisten. La actualización de valores institucionales edita el conjunto actual; no elimina ni añade valores mediante ese endpoint.

## Pagos

Los pedidos se crean siempre con pago **pendiente**, tanto para contraentrega como para transferencia. No se ofrece Wompi/tarjeta/PSE como pago funcionando. Se requiere una integración adicional con el proveedor y validación de webhooks para acreditar pagos reales; las claves vacías no habilitan esa integración.

## Verificar el funcionamiento real

1. Registra un producto con existencias reales y anota su stock.
2. Como cliente, crea una cotización y comprueba `quotes` y `quote_items` en SQL Editor.
3. Crea un pedido y comprueba `orders`, `order_items`, `order_tracking` y el descuento de stock.
4. Como administrador, consulta ambos módulos y cambia el estado de la cotización.
5. Asigna un mensajero; comprueba que solo ese mensajero puede operar sobre la entrega.
6. Reinicia el backend. Comprueba que el pedido y la cotización siguen disponibles.
7. Intenta consultar el pedido con otra cuenta cliente: no debe aparecer.
8. Prueba una cancelación permitida y comprueba que el stock se devuelve una sola vez.

Ejemplos SQL:

```sql
select quote_number, customer_name, status, created_at
from public.quotes order by created_at desc;

select order_number, customer_name, order_status, payment_status, total
from public.orders order by created_at desc;

select o.order_number, i.product_name, i.quantity, i.unit_price, i.subtotal
from public.order_items i join public.orders o on o.id=i.order_id;

select o.order_number, t.status, t.message, t.created_at
from public.order_tracking t join public.orders o on o.id=t.order_id
order by t.created_at;
```

## Pruebas y alcance de la validación

Se verifican unidades y contratos HTTP con servicios simulados, frontend y compilación. Además, `backend/tests/commerce_postgres_checks.py` ejecuta PostgreSQL real en una instancia local aislada con esquemas mínimos de Auth/Storage para comprobar SQL, rollback, stock, idempotencia, concurrencia y RLS. Esta prueba no modifica el Supabase remoto ni crea cuentas reales.

Para repetir la instalación, las reglas y la prueba en navegador en Windows con PostgreSQL instalado y Vite iniciado:

```powershell
uv run --no-project --with "psycopg[binary]" --with playwright --python backend/.venv/Scripts/python.exe python backend/tests/run_commerce_checks.py --browser
```

El ejecutor crea y detiene una instancia temporal dentro de `tmp`, sin tocar servicios PostgreSQL existentes. El navegador utiliza una identidad de prueba y un adaptador de transporte local hacia FastAPI y SQL reales; no certifica por sí solo el transporte PostgREST remoto.

Aplicar el SQL y completar una prueba con datos reales en el proyecto remoto sigue siendo necesario. El comando de verificación permite comprobar su estado sin imprimir credenciales.

Referencia de diseño: funciones de base de datos y privilegios de ejecución de Supabase: https://supabase.com/docs/guides/database/functions

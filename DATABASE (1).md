# DATABASE.md

# Diseño de base de datos propuesto para Neifit

Actualización de acceso: el catálogo completo ahora requiere sesión. Para bases existentes, aplicar `supabase/migrations/0002_catalogo_autenticado.sql`, que retira lectura anónima directa de `products` sin borrar datos. El esquema inicial ya incluye esta restricción para instalaciones nuevas. Las categorías de presentación y contenidos institucionales siguen siendo públicos; la muestra de productos se sirve de forma limitada desde FastAPI. No se aplicó esta migración a la instancia remota durante el cambio de interfaz. Ver `PLAN_AUTORIZACION.md`.

## 1. Objetivo

Definir una estructura de base de datos en Supabase/PostgreSQL para soportar el funcionamiento de Neifit.

## 2. Entidades principales

## 2.1 profiles
Extiende el usuario autenticado con datos de negocio.

Campos sugeridos:
- id
- full_name
- email
- role (`admin`, `mensajeria`, `cliente`)
- phone
- created_at
- updated_at

## 2.2 categories
Campos sugeridos:
- id
- name
- slug
- description
- is_active

Valores iniciales sugeridos:
- Postres
- Snacks
- Bebidas

## 2.3 products
Campos sugeridos:
- id
- category_id
- name
- slug
- description
- price
- stock
- is_available
- image_url
- featured
- created_at
- updated_at

## 2.4 carts
Campos sugeridos:
- id
- user_id
- status
- created_at
- updated_at

## 2.5 cart_items
Campos sugeridos:
- id
- cart_id
- product_id
- quantity
- unit_price
- subtotal

## 2.6 orders
Campos sugeridos:
- id
- user_id
- order_number
- order_status
- payment_status
- payment_method
- subtotal
- shipping_cost
- total
- notes
- assigned_delivery_user_id
- created_at
- updated_at

## 2.7 order_items
Campos sugeridos:
- id
- order_id
- product_id
- quantity
- unit_price
- subtotal

## 2.8 quotes
Campos sugeridos:
- id
- user_id
- quote_number
- status
- customer_name
- customer_phone
- customer_email
- notes
- created_at

## 2.9 quote_items
Campos sugeridos:
- id
- quote_id
- product_id
- quantity
- reference_price

## 2.10 order_tracking
Tabla para la trazabilidad del pedido.

Campos sugeridos:
- id
- order_id
- status
- message
- updated_by
- created_at

Estados sugeridos:
- recibido
- confirmado
- en_preparacion
- empacado
- despachado
- en_ruta
- entregado
- novedad
- cancelado

## 2.11 payment_transactions
Campos sugeridos:
- id
- order_id
- provider
- provider_reference
- amount
- currency
- status
- raw_response
- created_at

## 3. Relaciones principales

- `products` pertenece a `categories`
- `carts` pertenece a `profiles`
- `cart_items` pertenece a `carts` y `products`
- `orders` pertenece a `profiles`
- `order_items` pertenece a `orders` y `products`
- `quotes` pertenece a `profiles`
- `quote_items` pertenece a `quotes` y `products`
- `order_tracking` pertenece a `orders`
- `orders.assigned_delivery_user_id` apunta a `profiles`

## 4. Reglas de integridad

- `stock` no puede ser negativo.
- `price` debe ser mayor que cero.
- `quantity` debe ser mayor que cero.
- `order_number` debe ser único.
- `quote_number` debe ser único.

## 5. Seguridad y RLS

### Cliente
Puede:
- ver productos activos,
- gestionar su carrito,
- ver sus pedidos,
- ver sus cotizaciones,
- ver la trazabilidad de sus pedidos.

### Administrador
Puede:
- gestionar todo el catálogo,
- ver todos los pedidos,
- ver todas las cotizaciones,
- asignar pedidos,
- actualizar trazabilidad,
- gestionar inventario.

### Mensajería
Puede:
- ver pedidos asignados,
- ver datos logísticos necesarios,
- actualizar estado de entrega y trazabilidad.

## 6. Storage sugerido

Buckets sugeridos:
- `products` para imágenes de productos.
- `evidence` para soportes logísticos si luego se requieren.

## 7. Índices sugeridos

- índice por `category_id` en `products`
- índice por `user_id` en `orders`
- índice por `order_status` en `orders`
- índice por `order_id` en `order_tracking`
- índice por `quote_number` en `quotes`

## 8. Observación importante

Si se integra una pasarela como Wompi, Mercado Pago o PayU, la confirmación del pago deberá registrarse en `payment_transactions` y reflejarse en `orders.payment_status`.


## 9. Modelo para landing page y contenido institucional

### `site_content`
- `id`: UUID PK
- `key`: texto único (`about_us`, `mission`, `vision`, `hero_title`, `hero_description`)
- `title`: texto opcional
- `body`: texto no vacío
- `is_published`: booleano, predeterminado falso
- `updated_by`: UUID FK a `profiles.id`
- `updated_at`: timestamp con zona horaria

### `company_settings`
- `id`: UUID PK (instancia única de configuración)
- `business_name`: texto (`Neifit`)
- `phone_public`: texto nullable
- `whatsapp_number`: texto nullable en formato internacional
- `address`: texto nullable
- `city`: texto nullable
- `opening_hours`: JSONB nullable
- `map_url`: texto nullable; URL validada
- `logo_url`: texto nullable
- `updated_at`: timestamp con zona horaria

### `company_values`
- `id`: UUID PK
- `title`: texto
- `description`: texto
- `sort_order`: entero no negativo
- `is_published`: booleano

### Acceso y permisos

Visitantes y clientes pueden consultar **solo contenido publicado y campos de contacto públicos**. Solo administradores gestionan contenido o datos comerciales. No almacenar valores privados ni credenciales en estas tablas. El backend Python valida autorización y Supabase RLS refuerza el aislamiento.

## 10. Arquitectura de acceso a datos

Python FastAPI centraliza reglas transaccionales de inventario, pedidos, cotizaciones y pagos; utilizar transacciones PostgreSQL y políticas RLS adecuadas al contexto de ejecución. El navegador usa solamente la URL de API y las credenciales públicas de Supabase. Las claves privilegiadas y secretos de webhooks permanecen únicamente en servidor.

## 11. Migraciones pendientes

Actualización del 7 de noviembre de 2026: `supabase/neifit_inicial.sql` reúne esquema, seguridad, Storage y contenido inicial en una instalación transaccional para proyectos nuevos. `supabase/verificar_seguridad.sql` permite comprobar permisos después de ejecutarla. No se ha aplicado a una instancia remota. Las modificaciones posteriores deben entregarse como migraciones incrementales; no ejecutar este instalador sobre tablas preexistentes. Ver `CONEXION_SUPABASE.md`.

Las escrituras comerciales quedan reservadas al backend con `service_role`; RLS permite consulta pública del contenido publicado y consulta de datos propios. Admin y mensajería acceden mediante endpoints que comprueban permisos y asignación. Los usuarios solo tienen permiso de actualización de nombre y teléfono en su propio perfil, nunca del rol. La migración 0005 implementa creación atómica de pedidos/cotizaciones, inventario, idempotencia y seguimiento. Añade `shipping_cost` a la configuración, `request_id` y `request_fingerprint` a documentos, `stock_debited` a pedidos y `product_name` a detalles de cotización. Requiere activación en Supabase según PERSISTENCIA_SUPABASE.md.


## 12. Datos iniciales públicos configurables (para migración posterior)

Configuración prevista en `company_settings`:

```json
{
  "business_name": "Neifit",
  "phone_public": "+57 3127827020",
  "whatsapp_number": "573127827020",
  "address": "CR 28B # 38F - 56",
  "city": "Medellín",
  "opening_hours": {
    "timezone": "America/Bogota",
    "monday": "09:00-18:00",
    "tuesday": "09:00-18:00",
    "wednesday": "09:00-18:00",
    "thursday": "09:00-18:00",
    "friday": "09:00-18:00",
    "saturday": null,
    "sunday": null
  },
  "map_url": null
}
```

Crear registros `site_content` publicables (`about_us`, `mission`, `vision`) con los textos seleccionados en `DESIGN.md`, y seis registros en `company_values`. Evitar sembrar secretos o datos ficticios como coordenadas. Esta sección es **especificación**, no una migración SQL ejecutada.

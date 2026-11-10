-- DATOS FICTICIOS: consultas de solo lectura para SQL Editor.
-- Conjunto identificado por slugs y UUID, sin etiquetas en nombres o direcciones.
-- Los precios, existencias, clientes y solicitudes de esta carga son inventados.

-- 1. Cantidad de registros de prueba.
select 'Productos' as tabla,count(*) as registros
from public.products where slug like 'prueba-%'
union all
select 'Cotizaciones',count(*) from public.quotes where id in ('59fac4cc-62a1-4ce3-8640-a1fd2e14cee6'::uuid,'2dd93336-0328-46be-b56a-b7017aaa48ad'::uuid,'1d31b4d0-d5de-45be-b3c4-f1b6fe61ccc9'::uuid)
union all
select 'Pedidos',count(*) from public.orders where id in ('9774f803-9e89-45ac-b0f5-59ab6fb33a39'::uuid,'09a376d6-7ba0-447e-a4b0-d95cc2787fda'::uuid,'6140f9b3-8d5e-466c-a2f2-bd465b115aab'::uuid);

-- 2. Catálogo cargado: existencias actuales DESPUÉS de los pedidos.
select p.name,c.name as categoria,p.price,p.stock,
  (p.is_active and p.is_available and p.stock>0 and c.is_active) as disponible
from public.products p
join public.categories c on c.id=p.category_id
where p.slug like 'prueba-%'
order by c.name,p.name;

-- 3. Productos con pocas unidades (debe devolver registros).
select name,stock,price
from public.products
where is_active=true and stock<=5
order by stock,name;

-- 4. Cotizaciones pendientes y su importe de referencia (sin domicilio).
select q.quote_number,q.customer_name,q.status,q.created_at,
  coalesce(sum(i.quantity*i.reference_price),0) as total_referencia
from public.quotes q
left join public.quote_items i on i.quote_id=q.id
where q.status='pendiente'
group by q.id,q.quote_number,q.customer_name,q.status,q.created_at
order by q.created_at;

-- 5. Pedidos pendientes de entrega con responsable asignado.
-- En dos pedidos de prueba el responsable es el administrador, sin cambiar su rol.
select p.full_name as responsable,p.role as rol_responsable,o.order_number,
  o.customer_name,o.address,o.order_status,o.payment_status
from public.orders o
join public.profiles p on p.id=o.assigned_delivery_user_id
where o.order_status not in ('entregado','cancelado')
order by p.full_name,o.created_at;

-- 6. Unidades SOLICITADAS en pedidos de prueba pendientes de pago.
-- No representa ventas cobradas ni ingresos confirmados.
select p.name,sum(i.quantity) as unidades_solicitadas,
  sum(i.subtotal) as importe_solicitado
from public.order_items i
join public.orders o on o.id=i.order_id
join public.products p on p.id=i.product_id
where o.id in ('9774f803-9e89-45ac-b0f5-59ab6fb33a39'::uuid,'09a376d6-7ba0-447e-a4b0-d95cc2787fda'::uuid,'6140f9b3-8d5e-466c-a2f2-bd465b115aab'::uuid) and o.order_status<>'cancelado'
  and o.payment_status='pendiente'
group by p.id,p.name
order by unidades_solicitadas desc,p.name;

-- 7. Historial de los pedidos.
select o.order_number,t.status,t.message,t.created_at
from public.order_tracking t join public.orders o on o.id=t.order_id
where o.id in ('9774f803-9e89-45ac-b0f5-59ab6fb33a39'::uuid,'09a376d6-7ba0-447e-a4b0-d95cc2787fda'::uuid,'6140f9b3-8d5e-466c-a2f2-bd465b115aab'::uuid)
order by o.created_at,t.created_at;

-- 8. Usuarios y roles existentes. No se crean cuentas ficticias ni se cambian roles.
select p.full_name,p.email,r.name as rol
from public.profiles p join public.access_roles r on r.code=p.role
order by r.name,p.full_name;

-- 9. Productos en pedidos aprobados del conjunto de presentacion.
-- Existen dos aprobaciones simuladas, identificadas en payment_transactions.raw_response; no representan cobros reales.
select p.name,sum(i.quantity) as unidades,sum(i.subtotal) as importe_productos
from public.order_items i
join public.orders o on o.id=i.order_id
join public.products p on p.id=i.product_id
where o.payment_status='aprobado' and o.order_status<>'cancelado'
group by p.id,p.name order by unidades desc;

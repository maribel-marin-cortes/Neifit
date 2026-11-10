-- PostgreSQL: cinco consultas de solo lectura para la exposición.
-- Requieren tablas instaladas, datos persistidos y autorización.

-- Productos con pocas unidades
select name, stock, price
from public.products
where is_active = true
  and stock <= 5
order by stock asc, name;

-- Cotizaciones pendientes
select q.quote_number, q.customer_name, q.created_at,
  coalesce(sum(qi.quantity * qi.reference_price), 0)
    as total_referencia
from public.quotes q
left join public.quote_items qi on qi.quote_id = q.id
where q.status = 'pendiente'
group by q.id, q.quote_number, q.customer_name, q.created_at
order by q.created_at;

-- Entregas por mensajero
select p.full_name as mensajero, o.order_number,
  o.customer_name, o.address, o.order_status
from public.orders o
join public.profiles p
  on p.id = o.assigned_delivery_user_id
where o.order_status not in ('entregado', 'cancelado')
order by p.full_name, o.created_at;

-- Productos con más unidades vendidas
select oi.product_id, p.name,
  sum(oi.quantity) as unidades,
  sum(oi.subtotal) as importe_productos
from public.order_items oi
join public.orders o on o.id = oi.order_id
join public.products p on p.id = oi.product_id
where o.payment_status = 'aprobado'
  and o.order_status <> 'cancelado'
group by oi.product_id, p.name
order by unidades desc;

-- Usuarios y sus roles
select p.full_name, p.email, r.name as rol
from public.profiles p
join public.access_roles r on r.code = p.role
order by r.name, p.full_name;

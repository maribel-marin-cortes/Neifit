"""Consultas solicitadas para la exposición: PostgreSQL, solo lectura."""
CONSULTAS = [
    ('Productos con pocas unidades', 'Identificar productos activos con cinco unidades o menos.',
     'Reposición', 'Permite priorizar la revisión del inventario. Incluye productos agotados.',
     "select name, stock, price\nfrom public.products\nwhere is_active = true\n  and stock <= 5\norder by stock asc, name;"),
    ('Cotizaciones pendientes', 'Consultar las solicitudes sin responder y su importe de referencia.',
     'Atención comercial', 'El importe suma cantidad × precio de referencia; no incluye domicilio ni es un pago confirmado.',
     "select q.quote_number, q.customer_name, q.created_at,\n  coalesce(sum(qi.quantity * qi.reference_price), 0)\n    as total_referencia\nfrom public.quotes q\nleft join public.quote_items qi on qi.quote_id = q.id\nwhere q.status = 'pendiente'\ngroup by q.id, q.quote_number, q.customer_name, q.created_at\norder by q.created_at;"),
    ('Entregas por mensajero', 'Consultar pedidos asignados que aún no están entregados ni cancelados.',
     'Logística', 'Muestra responsable, cliente, dirección y estado. El JOIN excluye pedidos sin mensajero asignado.',
     "select p.full_name as mensajero, o.order_number,\n  o.customer_name, o.address, o.order_status\nfrom public.orders o\njoin public.profiles p\n  on p.id = o.assigned_delivery_user_id\nwhere o.order_status not in ('entregado', 'cancelado')\norder by p.full_name, o.created_at;"),
    ('Productos con más unidades vendidas', 'Sumar unidades e importes de pedidos no cancelados con pago aprobado.',
     'Análisis comercial', 'Agrupa por producto. El importe corresponde a sus detalles, sin sumar el domicilio.',
     "select oi.product_id, p.name,\n  sum(oi.quantity) as unidades,\n  sum(oi.subtotal) as importe_productos\nfrom public.order_items oi\njoin public.orders o on o.id = oi.order_id\njoin public.products p on p.id = oi.product_id\nwhere o.payment_status = 'aprobado'\n  and o.order_status <> 'cancelado'\ngroup by oi.product_id, p.name\norder by unidades desc;"),
    ('Usuarios y sus roles', 'Relacionar las cuentas registradas con el nombre de su rol.',
     'Administración de accesos', 'Permite revisar asignaciones. Requiere la tabla access_roles y una cuenta autorizada.',
     "select p.full_name, p.email, r.name as rol\nfrom public.profiles p\njoin public.access_roles r on r.code = p.role\norder by r.name, p.full_name;"),
]

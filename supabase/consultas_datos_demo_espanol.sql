-- Consultas de verificación para el conjunto inventado del esquema español.
-- Dos pagos están marcados como simulados y no representan fondos reales.

select 'Productos' tabla,count(*) registros from public.productos
where empresa_id=(select id from public.empresas where slug='neifit') and identificador_url like 'prueba-%'
union all
select 'Cotizaciones',count(*) from public.cotizaciones
where empresa_id=(select id from public.empresas where slug='neifit')
 and correo_cliente in ('camila.torres@example.com','mateo.rios@example.com','laura.gomez@example.com')
union all
select 'Pedidos',count(*) from public.pedidos
where empresa_id=(select id from public.empresas where slug='neifit')
 and correo_cliente in ('camila.torres@example.com','mateo.rios@example.com','laura.gomez@example.com');

select p.nombre,c.nombre categoria,p.precio,p.existencias,
 (p.activo and p.disponible and p.existencias>0 and c.activo) disponible
from public.productos p join public.categorias c
 on c.empresa_id=p.empresa_id and c.id=p.categoria_id
where p.empresa_id=(select id from public.empresas where slug='neifit')
  and p.identificador_url like 'prueba-%'
order by c.nombre,p.nombre;

select q.numero_cotizacion,q.nombre_cliente,q.estado,q.creado_en,
 coalesce(sum(i.cantidad*i.precio_referencia),0) total_referencia
from public.cotizaciones q left join public.elementos_cotizacion i
 on i.empresa_id=q.empresa_id and i.cotizacion_id=q.id
where q.empresa_id=(select id from public.empresas where slug='neifit')
 and q.correo_cliente in ('camila.torres@example.com','mateo.rios@example.com','laura.gomez@example.com')
group by q.id order by q.creado_en;

select o.numero_pedido,o.nombre_cliente,o.estado_pedido,o.estado_pago,o.total,
 exists(select 1 from public.transacciones_pago t where t.empresa_id=o.empresa_id
   and t.pedido_id=o.id and t.respuesta_cruda->>'simulated'='true') pago_simulado
from public.pedidos o
where o.empresa_id=(select id from public.empresas where slug='neifit')
 and o.correo_cliente in ('camila.torres@example.com','mateo.rios@example.com','laura.gomez@example.com')
order by o.creado_en;

select e.slug,p.correo,m.rol,m.estado
from public.miembros_empresa m join public.empresas e on e.id=m.empresa_id
join public.perfiles p on p.id=m.usuario_id
where e.slug='neifit' order by m.rol,p.correo;

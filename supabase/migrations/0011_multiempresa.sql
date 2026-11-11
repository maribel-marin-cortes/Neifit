-- Neifit multiempresa: aislamiento lógico por empresa sin borrar datos.
-- Requiere el esquema físico en español y 0010_ajustes_esquema_espanol.sql.
begin;

do $$ begin
  if to_regclass('public.productos') is null or to_regclass('public.notificaciones') is null then
    raise exception 'Primero instala el esquema completo en español y la migración 0010';
  end if;
end $$;

create table public.empresas (
  id uuid primary key default gen_random_uuid(),
  nombre text not null check(length(btrim(nombre)) between 3 and 100),
  slug text not null unique check(slug ~ '^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$'),
  estado text not null default 'activa' check(estado in ('activa','suspendida','inactiva')),
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create table public.miembros_empresa (
  empresa_id uuid not null references public.empresas(id) on delete cascade,
  usuario_id uuid not null references public.perfiles(id) on delete cascade,
  rol text not null references public.roles_acceso(codigo),
  estado text not null default 'activo' check(estado in ('activo','invitado','suspendido')),
  creado_en timestamptz not null default now(),
  primary key(empresa_id,usuario_id)
);
create index miembros_empresa_usuario on public.miembros_empresa(usuario_id,empresa_id);

insert into public.empresas(id,nombre,slug)
values('00000000-0000-0000-0000-000000000001','Neifit','neifit');
insert into public.miembros_empresa(empresa_id,usuario_id,rol)
select '00000000-0000-0000-0000-000000000001',id,rol from public.perfiles;

create function public.neifit_empresa_contexto() returns uuid
language sql stable set search_path='' as $$
 select nullif(pg_catalog.current_setting('app.empresa_id',true),'')::uuid
$$;

do $$
declare tabla text;
begin
 foreach tabla in array array[
  'categorias','productos','carritos','pedidos','cotizaciones','contenido_sitio',
  'configuracion_empresa','valores_empresa','direcciones_cliente','notificaciones'
 ] loop
   execute format('alter table public.%I add column empresa_id uuid references public.empresas(id)',tabla);
   execute format('update public.%I set empresa_id=$1 where empresa_id is null',tabla)
     using '00000000-0000-0000-0000-000000000001'::uuid;
   execute format('alter table public.%I alter column empresa_id set not null',tabla);
   execute format('alter table public.%I alter column empresa_id set default public.neifit_empresa_contexto()',tabla);
   execute format('create index %I on public.%I(empresa_id)',tabla||'_empresa_idx',tabla);
 end loop;
end $$;

-- Los detalles heredan la empresa de su cabecera y la guardan para RLS e integridad.
alter table public.elementos_carrito add column empresa_id uuid references public.empresas(id);
update public.elementos_carrito i set empresa_id=c.empresa_id from public.carritos c where c.id=i.carrito_id;
alter table public.elementos_carrito alter column empresa_id set not null;
alter table public.elementos_carrito alter column empresa_id set default public.neifit_empresa_contexto();
alter table public.elementos_pedido add column empresa_id uuid references public.empresas(id);
update public.elementos_pedido i set empresa_id=o.empresa_id from public.pedidos o where o.id=i.pedido_id;
alter table public.elementos_pedido alter column empresa_id set not null;
alter table public.elementos_pedido alter column empresa_id set default public.neifit_empresa_contexto();
alter table public.elementos_cotizacion add column empresa_id uuid references public.empresas(id);
update public.elementos_cotizacion i set empresa_id=q.empresa_id from public.cotizaciones q where q.id=i.cotizacion_id;
alter table public.elementos_cotizacion alter column empresa_id set not null;
alter table public.elementos_cotizacion alter column empresa_id set default public.neifit_empresa_contexto();
alter table public.seguimiento_pedidos add column empresa_id uuid references public.empresas(id);
update public.seguimiento_pedidos t set empresa_id=o.empresa_id from public.pedidos o where o.id=t.pedido_id;
alter table public.seguimiento_pedidos alter column empresa_id set not null;
alter table public.seguimiento_pedidos alter column empresa_id set default public.neifit_empresa_contexto();
alter table public.transacciones_pago add column empresa_id uuid references public.empresas(id);
update public.transacciones_pago t set empresa_id=o.empresa_id from public.pedidos o where o.id=t.pedido_id;
alter table public.transacciones_pago alter column empresa_id set not null;
alter table public.transacciones_pago alter column empresa_id set default public.neifit_empresa_contexto();

-- Las claves compuestas impiden relacionar accidentalmente registros de dos empresas.
alter table public.categorias add constraint categorias_empresa_id_id_key unique(empresa_id,id);
alter table public.productos add constraint productos_empresa_id_id_key unique(empresa_id,id);
alter table public.carritos add constraint carritos_empresa_id_id_key unique(empresa_id,id);
alter table public.pedidos add constraint pedidos_empresa_id_id_key unique(empresa_id,id);
alter table public.cotizaciones add constraint cotizaciones_empresa_id_id_key unique(empresa_id,id);
alter table public.productos drop constraint productos_categoria_id_fkey;
alter table public.productos add constraint productos_categoria_empresa_fkey
 foreign key(empresa_id,categoria_id) references public.categorias(empresa_id,id);
alter table public.elementos_carrito drop constraint elementos_carrito_carrito_id_fkey;
alter table public.elementos_carrito add constraint elementos_carrito_empresa_fkey
 foreign key(empresa_id,carrito_id) references public.carritos(empresa_id,id) on delete cascade;
alter table public.elementos_carrito drop constraint elementos_carrito_producto_id_fkey;
alter table public.elementos_carrito add constraint elementos_carrito_producto_empresa_fkey
 foreign key(empresa_id,producto_id) references public.productos(empresa_id,id);
alter table public.elementos_pedido drop constraint elementos_pedido_pedido_id_fkey;
alter table public.elementos_pedido add constraint elementos_pedido_empresa_fkey
 foreign key(empresa_id,pedido_id) references public.pedidos(empresa_id,id) on delete cascade;
alter table public.elementos_pedido drop constraint elementos_pedido_producto_id_fkey;
alter table public.elementos_pedido add constraint elementos_pedido_producto_empresa_fkey
 foreign key(empresa_id,producto_id) references public.productos(empresa_id,id);
alter table public.elementos_cotizacion drop constraint elementos_cotizacion_cotizacion_id_fkey;
alter table public.elementos_cotizacion add constraint elementos_cotizacion_empresa_fkey
 foreign key(empresa_id,cotizacion_id) references public.cotizaciones(empresa_id,id) on delete cascade;
alter table public.elementos_cotizacion drop constraint elementos_cotizacion_producto_id_fkey;
alter table public.elementos_cotizacion add constraint elementos_cotizacion_producto_empresa_fkey
 foreign key(empresa_id,producto_id) references public.productos(empresa_id,id);
alter table public.seguimiento_pedidos drop constraint seguimiento_pedidos_pedido_id_fkey;
alter table public.seguimiento_pedidos add constraint seguimiento_pedidos_empresa_fkey
 foreign key(empresa_id,pedido_id) references public.pedidos(empresa_id,id) on delete cascade;
alter table public.transacciones_pago drop constraint transacciones_pago_pedido_id_fkey;
alter table public.transacciones_pago add constraint transacciones_pago_empresa_fkey
 foreign key(empresa_id,pedido_id) references public.pedidos(empresa_id,id);

-- Unicidad dentro de cada comercio, no en toda la plataforma.
alter table public.categorias drop constraint categorias_identificador_url_key;
alter table public.categorias add constraint categorias_empresa_slug_key unique(empresa_id,identificador_url);
alter table public.productos drop constraint productos_identificador_url_key;
alter table public.productos add constraint productos_empresa_slug_key unique(empresa_id,identificador_url);
alter table public.contenido_sitio drop constraint contenido_sitio_clave_key;
alter table public.contenido_sitio add constraint contenido_sitio_empresa_clave_key unique(empresa_id,clave);
alter table public.valores_empresa drop constraint valores_empresa_titulo_key;
alter table public.valores_empresa add constraint valores_empresa_empresa_titulo_key unique(empresa_id,titulo);
alter table public.configuracion_empresa drop constraint configuracion_empresa_registro_unico_key;
alter table public.configuracion_empresa add constraint configuracion_empresa_empresa_key unique(empresa_id);
drop index carts_one_active_per_user;
create unique index carritos_activo_empresa_usuario on public.carritos(empresa_id,usuario_id) where estado='activo';
drop index orders_request_once;
create unique index pedidos_solicitud_empresa on public.pedidos(empresa_id,usuario_id,solicitud_id);
drop index quotes_request_once;
create unique index cotizaciones_solicitud_empresa on public.cotizaciones(empresa_id,usuario_id,solicitud_id);

alter table public.empresas enable row level security;
alter table public.miembros_empresa enable row level security;
revoke all on public.empresas,public.miembros_empresa from public,anon,authenticated;
grant select on public.empresas to anon,authenticated,service_role;
grant select on public.miembros_empresa to authenticated,service_role;
grant insert,update,delete on public.empresas,public.miembros_empresa to service_role;
create policy empresas_publicas on public.empresas for select to anon,authenticated using(estado='activa');
create policy membresia_propia on public.miembros_empresa for select to authenticated using(usuario_id=(select auth.uid()));

create function public.neifit_es_miembro(p_empresa uuid,p_usuario uuid default auth.uid()) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.miembros_empresa m join public.empresas e on e.id=m.empresa_id
  where m.empresa_id=p_empresa and m.usuario_id=p_usuario and m.estado='activo' and e.estado='activa')
$$;
revoke all on function public.neifit_empresa_contexto(),public.neifit_es_miembro(uuid,uuid) from public,anon;
grant execute on function public.neifit_es_miembro(uuid,uuid) to authenticated,service_role;

alter policy products_public on public.productos using(
 activo and public.neifit_es_miembro(empresa_id)
 and exists(select 1 from public.categorias c where c.id=categoria_id and c.empresa_id=productos.empresa_id and c.activo));
alter policy orders_read_self on public.pedidos using(
 usuario_id=(select auth.uid()) and public.neifit_es_miembro(empresa_id));
alter policy quotes_read_self on public.cotizaciones using(
 usuario_id=(select auth.uid()) and public.neifit_es_miembro(empresa_id));
alter policy carts_read_self on public.carritos using(
 usuario_id=(select auth.uid()) and public.neifit_es_miembro(empresa_id));
alter policy addresses_read_self on public.direcciones_cliente using(
 usuario_id=(select auth.uid()) and public.neifit_es_miembro(empresa_id));
alter policy notifications_read_self on public.notificaciones using(
 usuario_id=(select auth.uid()) and public.neifit_es_miembro(empresa_id));

-- La comprobación de permisos ahora usa el rol de la membresía, no el rol global del perfil.
create or replace function public.neifit_actor_puede(p_actor uuid,p_codigo text) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.miembros_empresa m
  where m.empresa_id=public.neifit_empresa_contexto() and m.usuario_id=p_actor and m.estado='activo'
  and (m.rol='admin' and exists(select 1 from public.permisos where codigo=p_codigo)
    or exists(select 1 from public.permisos_rol rp where rp.rol=m.rol and rp.codigo_permiso=p_codigo)))
$$;

create function public.neifit_crear_empresa(p_actor uuid,p_nombre text,p_slug text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare nueva public.empresas%rowtype;
begin
 if not exists(select 1 from public.perfiles where id=p_actor) then
   raise exception 'Perfil no autorizado' using errcode='42501';
 end if;
 if p_nombre is null or length(btrim(p_nombre)) not between 3 and 100
    or p_slug is null or p_slug !~ '^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$' then
   raise exception 'Nombre o identificador de empresa inválido' using errcode='22023';
 end if;
 insert into public.empresas(nombre,slug) values(btrim(p_nombre),lower(p_slug)) returning * into nueva;
 insert into public.miembros_empresa(empresa_id,usuario_id,rol) values(nueva.id,p_actor,'admin');
 insert into public.configuracion_empresa(empresa_id,nombre_negocio) values(nueva.id,nueva.nombre);
 insert into public.contenido_sitio(empresa_id,clave,titulo,cuerpo,publicado) values
  (nueva.id,'hero_title','Portada',nueva.nombre,true),
  (nueva.id,'hero_description','Presentación','Conoce nuestros productos y servicios.',true),
  (nueva.id,'about_us','Quiénes somos','Información pendiente de completar por la empresa.',true),
  (nueva.id,'mission','Misión','Información pendiente de completar por la empresa.',true),
  (nueva.id,'vision','Visión','Información pendiente de completar por la empresa.',true);
 return jsonb_build_object('id',nueva.id,'nombre',nueva.nombre,'slug',nueva.slug,'estado',nueva.estado,'rol','admin');
end $$;

create function public.neifit_asignar_rol(p_actor_id uuid,p_usuario_id uuid,p_rol text,p_empresa uuid)
returns void language plpgsql security definer set search_path='' as $$
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if p_actor_id=p_usuario_id or not exists(select 1 from public.miembros_empresa
    where empresa_id=p_empresa and usuario_id=p_actor_id and rol='admin' and estado='activo')
    or not exists(select 1 from public.roles_acceso where codigo=p_rol) then
   raise exception 'Cambio de rol no permitido' using errcode='42501';
 end if;
 insert into public.miembros_empresa(empresa_id,usuario_id,rol,estado)
 values(p_empresa,p_usuario_id,p_rol,'activo')
 on conflict(empresa_id,usuario_id) do update set rol=excluded.rol,estado='activo';
 insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
 values(p_actor_id,'assign_company_role',p_usuario_id::text,
  jsonb_build_object('empresa_id',p_empresa,'rol',p_rol));
end $$;

-- Sustituye la comprobación del antiguo rol global por la membresía empresarial activa.
create or replace function public.neifit_confirmar_efectivo(p_actor uuid,p_id uuid,p_importe numeric,p_referencia text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare pedido public.pedidos%rowtype;
begin
 if not exists(select 1 from public.miembros_empresa where empresa_id=public.neifit_empresa_contexto()
   and usuario_id=p_actor and rol='admin' and estado='activo') then
   raise exception 'Administrador requerido' using errcode='42501'; end if;
 select * into pedido from public.pedidos
 where id=p_id and empresa_id=public.neifit_empresa_contexto() for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if pedido.metodo_pago<>'contraentrega' or pedido.estado_pedido<>'entregado'
   or pedido.estado_pago not in ('pendiente','aprobado') then
   raise exception 'Solo se registra efectivo de pedidos contraentrega entregados' using errcode='P0001'; end if;
 if p_importe is distinct from pedido.total or length(trim(coalesce(p_referencia,''))) not between 3 and 200 then
   raise exception 'El importe debe coincidir con el pedido e incluir referencia del recibo' using errcode='22023'; end if;
 if pedido.estado_pago='aprobado' then
   if exists(select 1 from public.transacciones_pago where pedido_id=p_id and empresa_id=pedido.empresa_id
     and proveedor='contraentrega_manual') then return public.neifit_pedido_json(p_id); end if;
   raise exception 'El pedido ya tiene otro pago aprobado' using errcode='P0001';
 end if;
 insert into public.transacciones_pago(pedido_id,proveedor,referencia_proveedor,importe,moneda,estado,respuesta_cruda)
 values(p_id,'contraentrega_manual',p_id::text,p_importe,'COP','aprobado',
   jsonb_build_object('recorded_by',p_actor,'receipt',trim(p_referencia)));
 update public.pedidos set estado_pago='aprobado' where id=p_id and empresa_id=pedido.empresa_id;
 insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
 values(p_actor,'cash_received',p_id::text,jsonb_build_object('empresa_id',pedido.empresa_id,
   'importe',p_importe,'receipt',trim(p_referencia)));
 return public.neifit_pedido_json(p_id);
end $$;

-- Sobrecargas multiempresa. Establecen contexto transaccional antes de ejecutar las reglas existentes.
create function public.neifit_guardar_producto(p_actor uuid,p_datos jsonb,p_id uuid,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare resultado jsonb;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not public.neifit_actor_puede(p_actor,'products.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 if p_id is not null and not exists(select 1 from public.productos where id=p_id and empresa_id=p_empresa) then raise exception 'Producto no encontrado' using errcode='P0002'; end if;
 resultado:=public.neifit_guardar_producto(p_actor,p_datos,p_id);
 if resultado->>'empresa_id'<>p_empresa::text then raise exception 'Empresa incorrecta' using errcode='42501'; end if;
 return resultado;
end $$;

create function public.neifit_crear_documento(p_actor uuid,p_tipo text,p_solicitud uuid,p_datos jsonb,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare resultado jsonb;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not public.neifit_actor_puede(p_actor,case when p_tipo='order' then 'orders.create' else 'quotes.create' end) then raise exception 'Acceso denegado' using errcode='42501'; end if;
 if exists(select 1 from jsonb_array_elements(p_datos->'items') i where not exists(
   select 1 from public.productos p where p.id=(i->>'producto_id')::uuid and p.empresa_id=p_empresa)) then
   raise exception 'Uno o más productos no pertenecen a la empresa' using errcode='22023';
 end if;
 resultado:=public.neifit_crear_documento(p_actor,p_tipo,p_solicitud,p_datos);
 if resultado->>'empresa_id'<>p_empresa::text then raise exception 'Solicitud utilizada en otra empresa' using errcode='23505'; end if;
 return resultado;
end $$;

create function public.neifit_leer_pedidos(p_actor uuid,p_id uuid,p_seguimiento text,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare datos jsonb;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 datos:=public.neifit_leer_pedidos(p_actor,p_id,p_seguimiento);
 return coalesce((select jsonb_agg(x) from jsonb_array_elements(datos) x where x->>'empresa_id'=p_empresa::text),'[]'::jsonb);
end $$;

create function public.neifit_leer_cotizaciones(p_actor uuid,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare datos jsonb;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 datos:=public.neifit_leer_cotizaciones(p_actor);
 return coalesce((select jsonb_agg(x) from jsonb_array_elements(datos) x where x->>'empresa_id'=p_empresa::text),'[]'::jsonb);
end $$;

create function public.neifit_actualizar_pedido(p_actor uuid,p_id uuid,p_estado text,p_mensaje text,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$ begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.pedidos where id=p_id and empresa_id=p_empresa) then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 return public.neifit_actualizar_pedido(p_actor,p_id,p_estado,p_mensaje); end $$;
create function public.neifit_asignar_mensajero(p_actor uuid,p_id uuid,p_mensajero uuid,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$ begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.pedidos where id=p_id and empresa_id=p_empresa) then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 return public.neifit_asignar_mensajero(p_actor,p_id,p_mensajero); end $$;
create function public.neifit_actualizar_cotizacion(p_actor uuid,p_id uuid,p_estado text,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$ begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.cotizaciones where id=p_id and empresa_id=p_empresa) then raise exception 'Cotización no encontrada' using errcode='P0002'; end if;
 return public.neifit_actualizar_cotizacion(p_actor,p_id,p_estado); end $$;
create function public.neifit_responder_cotizacion(p_actor uuid,p_id uuid,p_total numeric,p_condiciones text,p_valida_hasta timestamptz,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$ begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.cotizaciones where id=p_id and empresa_id=p_empresa) then raise exception 'Cotización no encontrada' using errcode='P0002'; end if;
 return public.neifit_responder_cotizacion(p_actor,p_id,p_total,p_condiciones,p_valida_hasta); end $$;
create function public.neifit_confirmar_efectivo(p_actor uuid,p_id uuid,p_importe numeric,p_referencia text,p_empresa uuid) returns jsonb
language plpgsql security definer set search_path='' as $$ begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.pedidos where id=p_id and empresa_id=p_empresa) then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if not exists(select 1 from public.miembros_empresa where empresa_id=p_empresa and usuario_id=p_actor and rol='admin' and estado='activo') then raise exception 'Administrador requerido' using errcode='42501'; end if;
 return public.neifit_confirmar_efectivo(p_actor,p_id,p_importe,p_referencia); end $$;

do $$ declare firma text; begin
 foreach firma in array array[
  'neifit_guardar_producto(uuid,jsonb,uuid,uuid)','neifit_crear_documento(uuid,text,uuid,jsonb,uuid)',
  'neifit_leer_pedidos(uuid,uuid,text,uuid)','neifit_leer_cotizaciones(uuid,uuid)',
  'neifit_actualizar_pedido(uuid,uuid,text,text,uuid)','neifit_asignar_mensajero(uuid,uuid,uuid,uuid)',
  'neifit_actualizar_cotizacion(uuid,uuid,text,uuid)','neifit_responder_cotizacion(uuid,uuid,numeric,text,timestamptz,uuid)',
  'neifit_confirmar_efectivo(uuid,uuid,numeric,text,uuid)',
  'neifit_crear_empresa(uuid,text,text)','neifit_asignar_rol(uuid,uuid,text,uuid)'
 ] loop
  execute 'revoke all on function public.'||firma||' from public,anon,authenticated';
  execute 'grant execute on function public.'||firma||' to service_role';
 end loop;
end $$;

notify pgrst,'reload schema';
commit;

select e.slug,count(m.usuario_id) miembros from public.empresas e
left join public.miembros_empresa m on m.empresa_id=e.id group by e.id order by e.slug;

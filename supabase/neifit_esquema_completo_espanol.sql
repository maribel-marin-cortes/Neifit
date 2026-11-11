-- NEIFIT: INSTALADOR COMPLETO PARA UN PROYECTO SUPABASE NUEVO.
-- Esquema físico completo en español para una base public vacía. No elimina esquemas ni datos automáticamente.
-- Ejecutar TODO una sola vez en Supabase > SQL Editor.
-- No ejecutar además los archivos originales: ya están incluidos aquí.
-- No contiene claves, contraseñas ni copias de usuarios/pedidos del proyecto original.
-- Conserva las categorías y los contenidos institucionales iniciales de Neifit.
-- No es un instalador de PostgreSQL genérico: requiere Supabase Auth y Storage.

begin;
do $$
begin
  if to_regclass('auth.users') is null or to_regclass('storage.buckets') is null then
    raise exception 'Requiere un proyecto Supabase con Auth y Storage disponibles';
  end if;
  if exists(select 1 from pg_tables where schemaname = 'public'
    and tablename = any(array['perfiles','categorias','productos','carritos','elementos_carrito','pedidos','elementos_pedido','cotizaciones','elementos_cotizacion','seguimiento_pedidos','transacciones_pago','contenido_sitio','configuracion_empresa','valores_empresa','permisos','limites_permisos_rol','permisos_rol','auditoria_acceso','roles_acceso','direcciones_cliente','notificaciones'])) then
    raise exception 'Ya existen tablas de Neifit. Utiliza un proyecto nuevo o revisa las migraciones pendientes. No se ha borrado ningún dato.';
  end if;
end;
$$;


-- ==================== neifit_inicial.sql ====================
-- NEIFIT: ejecutar completo en SQL Editor de un proyecto Supabase NUEVO.
-- No ejecutar sobre tablas existentes con otra estructura.
-- Sin productos/precios/existencias ficticios. Las escrituras comerciales son del backend.

create table public.perfiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre_completo text not null default '',
  correo text,
  telefono text,
  rol text not null default 'cliente' check (rol in ('admin','mensajeria','cliente')),
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create table public.categorias (
  id uuid primary key default gen_random_uuid(),
  nombre text not null check (btrim(nombre) <> ''),
  identificador_url text not null unique,
  descripcion text not null default '',
  url_imagen text,
  activo boolean not null default true
);

create table public.productos (
  id uuid primary key default gen_random_uuid(),
  categoria_id uuid not null references public.categorias(id),
  nombre text not null check (btrim(nombre) <> ''),
  identificador_url text not null unique,
  descripcion text not null default '',
  ingredientes text,
  alergenos text,
  precio numeric(12,2) not null check (precio > 0),
  existencias integer not null default 0 check (existencias >= 0),
  activo boolean not null default true,
  disponible boolean not null default true,
  url_imagen text,
  destacado boolean not null default false,
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);
-- Disponibilidad efectiva: activo AND disponible AND existencias > 0.

create table public.carritos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles(id),
  estado text not null default 'activo' check (estado in ('activo','convertido','abandonado')),
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);
create unique index carts_one_active_per_user on public.carritos(usuario_id) where estado = 'activo';
create table public.elementos_carrito (
  id uuid primary key default gen_random_uuid(),
  carrito_id uuid not null references public.carritos(id) on delete cascade,
  producto_id uuid not null references public.productos(id),
  cantidad integer not null check (cantidad > 0),
  precio_unitario numeric(12,2) not null check (precio_unitario > 0),
  subtotal numeric(14,2) generated always as (cantidad * precio_unitario) stored,
  unique(carrito_id, producto_id)
);

create table public.pedidos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles(id),
  numero_pedido text not null unique default ('NF-' || gen_random_uuid()::text),
  nombre_cliente text not null,
  telefono_cliente text not null,
  correo_cliente text,
  direccion text not null,
  estado_pedido text not null default 'recibido' check (estado_pedido in
    ('recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado')),
  estado_pago text not null default 'pendiente' check (estado_pago in
    ('pendiente','aprobado','rechazado','reembolsado','cancelado')),
  metodo_pago text,
  subtotal numeric(14,2) not null check (subtotal >= 0),
  costo_envio numeric(12,2) not null default 0 check (costo_envio >= 0),
  total numeric(14,2) generated always as (subtotal + costo_envio) stored,
  notas text,
  usuario_mensajero_asignado_id uuid references public.perfiles(id),
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);
create table public.elementos_pedido (
  id uuid primary key default gen_random_uuid(),
  pedido_id uuid not null references public.pedidos(id) on delete cascade,
  producto_id uuid not null references public.productos(id),
  nombre_producto text not null,
  cantidad integer not null check (cantidad > 0),
  precio_unitario numeric(12,2) not null check (precio_unitario > 0),
  subtotal numeric(14,2) generated always as (cantidad * precio_unitario) stored,
  unique(pedido_id, producto_id)
);

create table public.cotizaciones (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles(id),
  numero_cotizacion text not null unique default ('COT-' || gen_random_uuid()::text),
  estado text not null default 'pendiente' check (estado in ('pendiente','respondida','aceptada','rechazada','cancelada')),
  nombre_cliente text not null,
  telefono_cliente text not null,
  correo_cliente text,
  notas text,
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);
create table public.elementos_cotizacion (
  id uuid primary key default gen_random_uuid(),
  cotizacion_id uuid not null references public.cotizaciones(id) on delete cascade,
  producto_id uuid not null references public.productos(id),
  cantidad integer not null check (cantidad > 0),
  precio_referencia numeric(12,2) not null check (precio_referencia > 0),
  unique(cotizacion_id, producto_id)
);
create table public.seguimiento_pedidos (
  id uuid primary key default gen_random_uuid(),
  pedido_id uuid not null references public.pedidos(id) on delete cascade,
  estado text not null check (estado in
    ('recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado')),
  mensaje text not null default '',
  actualizado_por uuid references public.perfiles(id),
  creado_en timestamptz not null default now()
);
create table public.transacciones_pago (
  id uuid primary key default gen_random_uuid(),
  pedido_id uuid not null references public.pedidos(id),
  proveedor text not null,
  referencia_proveedor text not null,
  importe numeric(14,2) not null check (importe > 0),
  moneda text not null default 'COP' check (moneda = 'COP'),
  estado text not null default 'pendiente' check (estado in
    ('pendiente','aprobado','rechazado','reembolsado','cancelado')),
  respuesta_cruda jsonb,
  creado_en timestamptz not null default now(),
  unique(proveedor, referencia_proveedor)
);

create table public.contenido_sitio (
  id uuid primary key default gen_random_uuid(),
  clave text not null unique,
  titulo text,
  cuerpo text not null check (btrim(cuerpo) <> ''),
  publicado boolean not null default false,
  actualizado_por uuid references public.perfiles(id),
  actualizado_en timestamptz not null default now()
);
create table public.configuracion_empresa (
  id uuid primary key default gen_random_uuid(),
  registro_unico boolean not null default true unique check (registro_unico),
  nombre_negocio text not null default 'Neifit',
  telefono_publico text,
  numero_whatsapp text check (numero_whatsapp ~ '^[1-9][0-9]{7,14}$'),
  direccion text,
  ciudad text,
  horario_atencion jsonb,
  url_mapa text check (url_mapa is null or url_mapa ~ '^https://'),
  url_logo text check (url_logo is null or url_logo ~ '^https://'),
  actualizado_en timestamptz not null default now()
);
create table public.valores_empresa (
  id uuid primary key default gen_random_uuid(),
  titulo text not null unique check (btrim(titulo) <> ''),
  descripcion text not null default '',
  orden integer not null default 0 check (orden >= 0),
  publicado boolean not null default false
);

create index products_category_idx on public.productos(categoria_id);
create index orders_user_idx on public.pedidos(usuario_id);
create index orders_status_idx on public.pedidos(estado_pedido);
create index orders_delivery_idx on public.pedidos(usuario_mensajero_asignado_id);
create index order_items_order_idx on public.elementos_pedido(pedido_id);
create index quotes_user_idx on public.cotizaciones(usuario_id);
create index quote_items_quote_idx on public.elementos_cotizacion(cotizacion_id);
create index tracking_order_idx on public.seguimiento_pedidos(pedido_id, creado_en);
create index payments_order_idx on public.transacciones_pago(pedido_id);

create function public.neifit_establecer_actualizado_en() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.actualizado_en = now();
  return new;
end;
$$;
do $$
declare table_name text;
begin
  foreach table_name in array array['perfiles','productos','carritos','pedidos','cotizaciones','contenido_sitio','configuracion_empresa'] loop
    execute format('create trigger neifit_updated_at before update on public.%I for each row execute function public.neifit_establecer_actualizado_en()', table_name);
  end loop;
end;
$$;

-- Ignora cualquier rol enviado en los metadatos del registro.
create function public.neifit_gestionar_usuario_nuevo() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.perfiles(id, correo, nombre_completo, telefono, rol)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'nombre_completo',new.raw_user_meta_data->>'full_name',''),
          coalesce(new.raw_user_meta_data->>'telefono',new.raw_user_meta_data->>'phone'), 'cliente');
  return new;
end;
$$;
create trigger neifit_auth_user_created after insert on auth.users
for each row execute function public.neifit_gestionar_usuario_nuevo();
-- Incluye usuarios que se hubieran registrado antes de ejecutar este archivo.
insert into public.perfiles(id, correo, nombre_completo, telefono)
select id, email, coalesce(raw_user_meta_data->>'nombre_completo',raw_user_meta_data->>'full_name',''), coalesce(raw_user_meta_data->>'telefono',raw_user_meta_data->>'phone')
from auth.users on conflict (id) do nothing;

-- RLS y privilegios explícitos. El navegador no modifica reglas comerciales.
do $$
declare table_name text;
begin
  foreach table_name in array array['perfiles','categorias','productos','carritos','elementos_carrito',
    'pedidos','elementos_pedido','cotizaciones','elementos_cotizacion','seguimiento_pedidos','transacciones_pago',
    'contenido_sitio','configuracion_empresa','valores_empresa'] loop
    execute format('alter table public.%I enable row level security', table_name);
    execute format('revoke all on table public.%I from anon, authenticated', table_name);
    execute format('grant all on table public.%I to service_role', table_name);
  end loop;
end;
$$;
grant usage on schema public to anon, authenticated, service_role;
grant select on public.categorias, public.contenido_sitio,
  public.configuracion_empresa, public.valores_empresa to anon, authenticated;
grant select on public.productos to authenticated;
grant select on public.perfiles, public.carritos, public.elementos_carrito, public.pedidos,
  public.elementos_pedido, public.cotizaciones, public.elementos_cotizacion, public.seguimiento_pedidos to authenticated;
-- El usuario puede corregir su nombre/teléfono, nunca rol, id ni correo.
grant update(nombre_completo, telefono) on public.perfiles to authenticated;
create policy profiles_read_self on public.perfiles for select to authenticated using (id = (select auth.uid()));
create policy profiles_update_self on public.perfiles for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));
create policy categories_public on public.categorias for select to anon, authenticated using (activo);
create policy products_public on public.productos for select to authenticated
  using (activo and exists (select 1 from public.categorias c where c.id = categoria_id and c.activo));
create policy content_public on public.contenido_sitio for select to anon, authenticated using (publicado);
create policy settings_public on public.configuracion_empresa for select to anon, authenticated using (true);
create policy values_public on public.valores_empresa for select to anon, authenticated using (publicado);
create policy carts_read_self on public.carritos for select to authenticated using (usuario_id = (select auth.uid()));
create policy cart_items_read_self on public.elementos_carrito for select to authenticated
  using (exists (select 1 from public.carritos c where c.id = carrito_id and c.usuario_id = (select auth.uid())));
create policy orders_read_self on public.pedidos for select to authenticated using (usuario_id = (select auth.uid()));
create policy order_items_read_self on public.elementos_pedido for select to authenticated
  using (exists (select 1 from public.pedidos o where o.id = pedido_id and o.usuario_id = (select auth.uid())));
create policy quotes_read_self on public.cotizaciones for select to authenticated using (usuario_id = (select auth.uid()));
create policy quote_items_read_self on public.elementos_cotizacion for select to authenticated
  using (exists (select 1 from public.cotizaciones q where q.id = cotizacion_id and q.usuario_id = (select auth.uid())));
create policy tracking_read_self on public.seguimiento_pedidos for select to authenticated
  using (exists (select 1 from public.pedidos o where o.id = pedido_id and o.usuario_id = (select auth.uid())));
-- Sin acceso directo a transacciones_pago (contiene respuesta privada del proveedor).
-- Admin/mensajería operan a través de FastAPI, que debe verificar rol/asignación.
revoke all on function public.neifit_gestionar_usuario_nuevo() from public, anon, authenticated;
revoke all on function public.neifit_establecer_actualizado_en() from public, anon, authenticated;

-- Storage: imágenes públicas de productos; evidencias privadas solo vía backend.
insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values ('productos','productos',true,5242880,array['image/jpeg','image/png','image/webp']),
       ('evidence','evidence',false,5242880,array['image/jpeg','image/png','image/webp','application/pdf'])
on conflict (id) do nothing;
-- No se conceden cargas/borrados al navegador. Usar backend o Dashboard.

insert into public.categorias(nombre, identificador_url, descripcion) values
 ('Postres','postres','Postres de la selección Neifit.'),
 ('Snacks','snacks','Snacks de la selección Neifit.'),
 ('Bebidas','bebidas','Bebidas de la selección Neifit.');
insert into public.configuracion_empresa(nombre_negocio, telefono_publico, numero_whatsapp, direccion, ciudad, horario_atencion)
values ('Neifit','+57 3127827020','573127827020','CR 28B # 38F - 56','Medellín, Antioquia, Colombia',
 '{"timezone":"America/Bogota","monday":"09:00-18:00","tuesday":"09:00-18:00","wednesday":"09:00-18:00","thursday":"09:00-18:00","friday":"09:00-18:00","saturday":null,"sunday":null}'::jsonb);
insert into public.contenido_sitio(clave, titulo, cuerpo, publicado) values
 ('hero_title','Portada','Sabores naturales que cuentan historias',true),
 ('hero_description','Presentación','Postres, snacks y bebidas con el sabor de nuestras raíces.',true),
 ('about_us','Quiénes somos','En Neifit reunimos sabores tradicionales, frutas y opciones para acompañar distintos momentos del día. Queremos que comprar sea una experiencia cercana y sencilla.',true),
 ('mission','Misión','Ofrecer una selección de postres, snacks y bebidas con atención cálida, información transparente y respeto por los sabores regionales.',true),
 ('vision','Visión','Ser una marca colombiana reconocida por conectar tradición, variedad y una experiencia de compra confiable.',true);
insert into public.valores_empresa(titulo, orden, publicado) values
 ('Calidad',1,true),('Transparencia',2,true),('Cercanía',3,true),
 ('Innovación',4,true),('Responsabilidad',5,true),('Tradición',6,true);

-- Comprobación: 14 tablas con RLS, 3 categorías, 5 contenidos, 6 valores.
select tablename, rowsecurity from pg_tables where schemaname = 'public'
and tablename in ('perfiles','categorias','productos','carritos','elementos_carrito','pedidos','elementos_pedido',
 'cotizaciones','elementos_cotizacion','seguimiento_pedidos','transacciones_pago','contenido_sitio','configuracion_empresa','valores_empresa')
order by tablename;


-- ==================== migrations/0002_catalogo_autenticado.sql ====================
-- Ejecutar una vez en SQL Editor si ya instalaste neifit_inicial.sql.
-- No reinstalar el esquema ni borrar datos.
-- La landing recibe una muestra controlada desde FastAPI /site/destacado-productos.
revoke select on table public.productos from anon;
alter policy products_public on public.productos to authenticated;

select has_table_privilege('anon','public.productos','SELECT') as anon_puede_leer_catalogo;
-- Debe devolver false. El contenido institucional sigue siendo público.


-- ==================== migrations/0003_roles_permisos.sql ====================
-- Ejecutar después del esquema inicial y 0002_catalogo_autenticado.sql.
-- No borra datos. Tras aplicarlo, activar RBAC_DATABASE_ENABLED=true en backend.
create table public.permisos (
  codigo text primary key,
  descripcion text not null
);
create table public.limites_permisos_rol (
  rol text not null check (rol in ('cliente','mensajeria','admin')),
  codigo_permiso text not null references public.permisos(codigo),
  primary key(rol, codigo_permiso)
);
create table public.permisos_rol (
  rol text not null,
  codigo_permiso text not null,
  primary key(rol, codigo_permiso),
  foreign key(rol, codigo_permiso) references public.limites_permisos_rol(rol, codigo_permiso)
);
create table public.auditoria_acceso (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid not null references public.perfiles(id),
  accion text not null,
  objetivo text not null,
  detalles jsonb not null,
  creado_en timestamptz not null default now()
);

insert into public.permisos(codigo,descripcion) values
('catalog.read','Consultar catálogo'),
('orders.create','Crear pedidos'),
('orders.read_own','Consultar pedidos propios'),
('quotes.create','Solicitar cotizaciones'),
('quotes.read_own','Consultar cotizaciones propias'),
('profile.read','Consultar perfil propio'),
('delivery.read_assigned','Consultar entregas asignadas'),
('delivery.start','Despachar e iniciar recorrido'),
('delivery.complete','Confirmar entrega'),
('delivery.issue','Registrar novedad'),
('products.manage','Gestionar productos e inventario'),
('orders.manage','Gestionar pedidos y asignaciones'),
('quotes.manage','Gestionar cotizaciones'),
('content.manage','Gestionar contenido institucional'),
('access.manage','Gestionar roles y permisos');
insert into public.limites_permisos_rol(rol,codigo_permiso) values
('cliente','catalog.read'),
('cliente','orders.create'),
('cliente','orders.read_own'),
('cliente','quotes.create'),
('cliente','quotes.read_own'),
('cliente','profile.read'),
('mensajeria','delivery.read_assigned'),
('mensajeria','delivery.start'),
('mensajeria','delivery.complete'),
('mensajeria','delivery.issue'),
('mensajeria','profile.read'),
('admin','catalog.read'),
('admin','orders.create'),
('admin','orders.read_own'),
('admin','quotes.create'),
('admin','quotes.read_own'),
('admin','profile.read'),
('admin','delivery.read_assigned'),
('admin','delivery.start'),
('admin','delivery.complete'),
('admin','delivery.issue'),
('admin','products.manage'),
('admin','orders.manage'),
('admin','quotes.manage'),
('admin','content.manage'),
('admin','access.manage');
insert into public.permisos_rol select * from public.limites_permisos_rol;

alter table public.permisos enable row level security;
alter table public.limites_permisos_rol enable row level security;
alter table public.permisos_rol enable row level security;
alter table public.auditoria_acceso enable row level security;
revoke all on public.permisos, public.limites_permisos_rol, public.permisos_rol, public.auditoria_acceso from anon, authenticated, service_role;
grant select on public.permisos, public.permisos_rol to authenticated;
grant select on public.permisos, public.limites_permisos_rol, public.permisos_rol, public.auditoria_acceso to service_role;
create policy permission_names on public.permisos for select to authenticated using (true);
create policy own_role_permissions on public.permisos_rol for select to authenticated
using (rol = (select p.rol from public.perfiles p where p.id = (select auth.uid())));

create function public.neifit_tiene_permiso(p_codigo text) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.perfiles p where p.id = auth.uid()
    and (p.rol = 'admin' and exists(select 1 from public.permisos where codigo = p_codigo)
      or exists(select 1 from public.permisos_rol rp where rp.rol = p.rol and rp.codigo_permiso = p_codigo))
  );
$$;
revoke all on function public.neifit_tiene_permiso(text) from public, anon;
grant execute on function public.neifit_tiene_permiso(text) to authenticated;

-- Solo FastAPI con clave de servidor puede invocar los cambios.
-- Ambas funciones serializan cambios y vuelven a comprobar el actor en BD.
create function public.neifit_asignar_rol(p_actor_id uuid, p_usuario_id uuid, p_rol text)
returns void language plpgsql security definer set search_path = '' as $$
declare rol_anterior text;
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.perfiles where id = p_actor_id and rol = 'admin') then
    raise exception 'Administrador requerido' using errcode='42501';
  end if;
  if p_actor_id = p_usuario_id or p_rol not in ('cliente','mensajeria','admin') then
    raise exception 'Cambio de rol no permitido' using errcode='42501';
  end if;
  select rol into rol_anterior from public.perfiles where id = p_usuario_id for update;
  if not found then raise exception 'Usuario no encontrado' using errcode='22023'; end if;
  if rol_anterior = 'admin' and p_rol <> 'admin'
    and (select count(*) from public.perfiles where rol = 'admin') <= 1 then
    raise exception 'Debe existir un administrador' using errcode='42501';
  end if;
  update public.perfiles set rol = p_rol where id = p_usuario_id;
  insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
  values(p_actor_id,'assign_role',p_usuario_id::text,jsonb_build_object('rol_anterior',rol_anterior,'rol',p_rol));
end;
$$;

create function public.neifit_establecer_permisos_rol(p_actor_id uuid, p_rol text, p_permisos text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.perfiles where id = p_actor_id and rol = 'admin')
    or p_rol not in ('cliente','mensajeria') then
    raise exception 'Cambio de permisos no permitido' using errcode='42501';
  end if;
  if p_permisos is null or not ('profile.read' = any(p_permisos)) then
    raise exception 'El perfil propio es un permiso obligatorio' using errcode='42501';
  end if;
  if exists(select 1 from unnest(p_permisos) codigo where codigo is null or not exists(
    select 1 from public.limites_permisos_rol l where l.rol = p_rol and l.codigo_permiso = codigo)) then
    raise exception 'Permiso fuera del alcance del rol' using errcode='42501';
  end if;
  delete from public.permisos_rol where rol = p_rol;
  insert into public.permisos_rol(rol,codigo_permiso) select p_rol, codigo from (select distinct unnest(p_permisos) codigo) s;
  insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
  values(p_actor_id,'set_permissions',p_rol,jsonb_build_object('permisos',p_permisos));
end;
$$;
revoke all on function public.neifit_asignar_rol(uuid,uuid,text) from public, anon, authenticated;
revoke all on function public.neifit_establecer_permisos_rol(uuid,text,text[]) from public, anon, authenticated;
grant execute on function public.neifit_asignar_rol(uuid,uuid,text), public.neifit_establecer_permisos_rol(uuid,text,text[]) to service_role;

-- Lectura por permiso y propiedad. Mensajería recibe datos por FastAPI con
-- proyección logística; no se le concede SELECT directo de pedidos completos.
alter policy products_public on public.productos using (
  activo and public.neifit_tiene_permiso('catalog.read')
  and exists(select 1 from public.categorias c where c.id = categoria_id and c.activo)
);
alter policy orders_read_self on public.pedidos using (usuario_id = (select auth.uid()) and public.neifit_tiene_permiso('orders.read_own'));
alter policy order_items_read_self on public.elementos_pedido using (public.neifit_tiene_permiso('orders.read_own') and exists(select 1 from public.pedidos o where o.id = pedido_id and o.usuario_id = (select auth.uid())));
alter policy tracking_read_self on public.seguimiento_pedidos using (public.neifit_tiene_permiso('orders.read_own') and exists(select 1 from public.pedidos o where o.id = pedido_id and o.usuario_id = (select auth.uid())));
alter policy quotes_read_self on public.cotizaciones using (usuario_id = (select auth.uid()) and public.neifit_tiene_permiso('quotes.read_own'));
alter policy quote_items_read_self on public.elementos_cotizacion using (public.neifit_tiene_permiso('quotes.read_own') and exists(select 1 from public.cotizaciones q where q.id = cotizacion_id and q.usuario_id = (select auth.uid())));
alter policy carts_read_self on public.carritos using (usuario_id = (select auth.uid()) and public.neifit_tiene_permiso('orders.create'));
alter policy cart_items_read_self on public.elementos_carrito using (public.neifit_tiene_permiso('orders.create') and exists(select 1 from public.carritos c where c.id = carrito_id and c.usuario_id = (select auth.uid())));

select rol, count(*) as permisos from public.permisos_rol group by rol order by rol;


-- ==================== migrations/0004_usuarios_roles_personalizados.sql ====================
-- Ejecutar después de 0003_roles_permisos.sql. No elimina usuarios ni datos.
create table public.roles_acceso (
  codigo text primary key check(codigo ~ '^[a-z][a-z0-9_]{2,39}$'),
  nombre text not null check(length(trim(nombre)) between 3 and 60),
  creado_en timestamptz not null default now()
);
insert into public.roles_acceso(codigo,nombre) values
 ('admin','Administrador'),('cliente','Cliente'),('mensajeria','Mensajero / domiciliario');
alter table public.perfiles drop constraint perfiles_rol_check;
alter table public.perfiles add constraint perfiles_rol_fkey foreign key(rol) references public.roles_acceso(codigo);
alter table public.limites_permisos_rol drop constraint limites_permisos_rol_rol_check;
alter table public.limites_permisos_rol add constraint limites_permisos_rol_rol_fkey foreign key(rol) references public.roles_acceso(codigo);
insert into public.permisos(codigo,descripcion) values ('users.manage','Gestionar usuarios y registrar mensajeros');
insert into public.limites_permisos_rol(rol,codigo_permiso) values ('admin','users.manage');
insert into public.permisos_rol(rol,codigo_permiso) values ('admin','users.manage');
alter table public.roles_acceso enable row level security;
revoke all on public.roles_acceso from public, anon, authenticated, service_role;
grant select on public.roles_acceso to service_role;
create or replace function public.neifit_asignar_rol(p_actor_id uuid, p_usuario_id uuid, p_rol text)
returns void language plpgsql security definer set search_path = '' as $$
declare rol_anterior text;
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.perfiles where id = p_actor_id and rol = 'admin') then
    raise exception 'Administrador requerido' using errcode='42501';
  end if;
  if p_actor_id = p_usuario_id or not exists(select 1 from public.roles_acceso where codigo = p_rol) then
    raise exception 'Cambio de rol no permitido' using errcode='42501';
  end if;
  select rol into rol_anterior from public.perfiles where id = p_usuario_id for update;
  if not found then raise exception 'Usuario no encontrado' using errcode='22023'; end if;
  if rol_anterior = 'admin' and p_rol <> 'admin'
    and (select count(*) from public.perfiles where rol = 'admin') <= 1 then
    raise exception 'Debe existir un administrador' using errcode='42501';
  end if;
  update public.perfiles set rol = p_rol where id = p_usuario_id;
  insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
  values(p_actor_id,'assign_role',p_usuario_id::text,jsonb_build_object('rol_anterior',rol_anterior,'rol',p_rol));
end;
$$;

create or replace function public.neifit_establecer_permisos_rol(p_actor_id uuid, p_rol text, p_permisos text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.perfiles where id = p_actor_id and rol = 'admin')
    or p_rol = 'admin' or not exists(select 1 from public.roles_acceso where codigo = p_rol) then
    raise exception 'Cambio de permisos no permitido' using errcode='42501';
  end if;
  if p_permisos is null or not ('profile.read' = any(p_permisos)) then
    raise exception 'El perfil propio es un permiso obligatorio' using errcode='42501';
  end if;
  if exists(select 1 from unnest(p_permisos) codigo where codigo is null or not exists(
    select 1 from public.limites_permisos_rol l where l.rol = p_rol and l.codigo_permiso = codigo)) then
    raise exception 'Permiso fuera del alcance del rol' using errcode='42501';
  end if;
  delete from public.permisos_rol where rol = p_rol;
  insert into public.permisos_rol(rol,codigo_permiso) select p_rol, codigo from (select distinct unnest(p_permisos) codigo) s;
  insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
  values(p_actor_id,'set_permissions',p_rol,jsonb_build_object('permisos',p_permisos));
end;
$$;
revoke all on function public.neifit_asignar_rol(uuid,uuid,text) from public, anon, authenticated;
revoke all on function public.neifit_establecer_permisos_rol(uuid,text,text[]) from public, anon, authenticated;
grant execute on function public.neifit_asignar_rol(uuid,uuid,text), public.neifit_establecer_permisos_rol(uuid,text,text[]) to service_role;


create function public.neifit_crear_rol(p_actor_id uuid, p_codigo text, p_nombre text, p_permisos text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.perfiles where id = p_actor_id and rol = 'admin') then
    raise exception 'Administrador requerido' using errcode='42501';
  end if;
  if p_codigo is null or p_codigo !~ '^[a-z][a-z0-9_]{2,39}$'
     or p_codigo in ('admin','cliente','mensajeria')
     or p_nombre is null or length(trim(p_nombre)) not between 3 and 60
     or p_permisos is null or not ('profile.read' = any(p_permisos)) then
    raise exception 'Rol o permisos inválidos' using errcode='22023';
  end if;
  if exists(select 1 from unnest(p_permisos) as requested(codigo) where requested.codigo is null
    or requested.codigo in ('access.manage','users.manage')
    or not exists(select 1 from public.permisos p where p.codigo = requested.codigo)) then
    raise exception 'Permisos no delegables' using errcode='42501';
  end if;
  insert into public.roles_acceso(codigo,nombre) values(p_codigo,trim(p_nombre));
  insert into public.limites_permisos_rol(rol,codigo_permiso)
    select p_codigo,codigo from public.permisos where codigo not in ('access.manage','users.manage');
  insert into public.permisos_rol(rol,codigo_permiso)
    select p_codigo,codigo from (select distinct unnest(p_permisos) codigo) s;
  insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
    values(p_actor_id,'create_role',p_codigo,jsonb_build_object('nombre',trim(p_nombre),'permisos',p_permisos));
end;
$$;
revoke all on function public.neifit_crear_rol(uuid,text,text,text[]) from public, anon, authenticated;
grant execute on function public.neifit_crear_rol(uuid,text,text,text[]) to service_role;
select codigo,nombre from public.roles_acceso order by nombre;


-- ==================== migrations/0005_servicios_comerciales.sql ====================
-- Persistencia comercial. Requiere esquema inicial y migraciones 0002-0004.
-- Ejecutable de nuevo sin borrar registros ni restablecer configuraciones.

alter table public.configuracion_empresa add column if not exists costo_envio numeric(12,2) not null default 5000 check(costo_envio >= 0);
alter table public.pedidos add column if not exists solicitud_id uuid not null default gen_random_uuid();
alter table public.pedidos add column if not exists huella_solicitud text;
alter table public.pedidos add column if not exists existencias_descontadas boolean not null default false;
alter table public.cotizaciones add column if not exists solicitud_id uuid not null default gen_random_uuid();
alter table public.cotizaciones add column if not exists huella_solicitud text;
alter table public.elementos_cotizacion add column if not exists nombre_producto text not null default '';
update public.elementos_cotizacion qi set nombre_producto=p.nombre from public.productos p where p.id=qi.producto_id and qi.nombre_producto='';
create unique index if not exists orders_request_once on public.pedidos(usuario_id,solicitud_id);
create unique index if not exists quotes_request_once on public.cotizaciones(usuario_id,solicitud_id);

-- Solo servidor. El actor siempre proviene del JWT validado por FastAPI.
create or replace function public.neifit_actor_puede(p_actor uuid,p_codigo text) returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.perfiles p where p.id=p_actor and (
    p.rol='admin' and exists(select 1 from public.permisos where codigo=p_codigo)
    or exists(select 1 from public.permisos_rol rp where rp.rol=p.rol and rp.codigo_permiso=p_codigo)));
$$;

create or replace function public.neifit_producto_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(p) || jsonb_build_object('category_name',c.nombre,'category_slug',c.identificador_url,'sales_enabled',p.disponible,
   'disponible',p.activo and p.disponible and p.existencias>0 and c.activo)
 from public.productos p join public.categorias c on c.id=p.categoria_id where p.id=p_id;
$$;

create or replace function public.neifit_pedido_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(o) - 'huella_solicitud' || jsonb_build_object(
   'assigned_delivery_name',p.nombre_completo,
   'items',coalesce((select jsonb_agg(to_jsonb(i) order by i.id) from public.elementos_pedido i where i.pedido_id=o.id),'[]'::jsonb),
   'tracking_history',coalesce((select jsonb_agg(jsonb_build_object('estado',t.estado,'mensaje',t.mensaje,'timestamp',t.creado_en) order by t.creado_en,t.id)
     from public.seguimiento_pedidos t where t.pedido_id=o.id),'[]'::jsonb))
 from public.pedidos o left join public.perfiles p on p.id=o.usuario_mensajero_asignado_id where o.id=p_id;
$$;

create or replace function public.neifit_cotizacion_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(q) - 'huella_solicitud' || jsonb_build_object(
   'items',coalesce((select jsonb_agg(to_jsonb(i) order by i.id) from public.elementos_cotizacion i where i.cotizacion_id=q.id),'[]'::jsonb))
 from public.cotizaciones q where q.id=p_id;
$$;

create or replace function public.neifit_crear_documento(p_actor uuid,p_tipo text,p_solicitud uuid,p_datos jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
  v_id uuid; v_old_hash text; v_hash text; v_items jsonb; v_item record;
  v_product public.productos%rowtype; v_total numeric(14,2):=0; v_shipping numeric(12,2);
  v_payment text; v_locked integer:=0;
begin
  if p_tipo not in ('order','quote') or p_tipo is null or p_solicitud is null then
    raise exception 'Solicitud inválida' using errcode='22023'; end if;
  if not public.neifit_actor_puede(p_actor,case when p_tipo='order' then 'orders.create' else 'quotes.create' end) then
    raise exception 'No tienes permiso para crear esta solicitud' using errcode='42501'; end if;
  if jsonb_typeof(p_datos->'items') is distinct from 'array' or jsonb_array_length(p_datos->'items') not between 1 and 100 then
    raise exception 'Incluye entre 1 y 100 productos' using errcode='22023'; end if;
  if length(btrim(coalesce(p_datos->>'nombre_cliente',''))) not between 3 and 100
    or length(btrim(coalesce(p_datos->>'telefono_cliente',''))) not between 7 and 30 then
    raise exception 'Nombre y teléfono inválidos' using errcode='22023'; end if;
  if exists(select 1 from jsonb_array_elements(p_datos->'items') i where
    jsonb_typeof(i->'cantidad') is distinct from 'number' or (i->>'cantidad') !~ '^[0-9]+$'
    or (i->>'cantidad')::numeric not between 1 and 10000 or i->>'producto_id' is null) then
    raise exception 'Productos o cantidades inválidos' using errcode='22023'; end if;
  select jsonb_agg(jsonb_build_object('producto_id',id,'cantidad',qty) order by id) into v_items from (
    select (i->>'producto_id')::uuid as id,sum((i->>'cantidad')::integer) as qty
    from jsonb_array_elements(p_datos->'items') i group by (i->>'producto_id')::uuid
  ) x;
  if exists(select 1 from jsonb_array_elements(v_items) i where (i->>'cantidad')::integer>10000) then
    raise exception 'Cantidad máxima superada' using errcode='22023'; end if;
  -- Ignorar los precios, totales y propietario declarados por el navegador.
  v_hash:=md5((jsonb_build_object('items',v_items,'nombre',p_datos->>'nombre_cliente','telefono',p_datos->>'telefono_cliente',
    'correo',p_datos->>'correo_cliente','direccion',p_datos->>'direccion','notas',p_datos->>'notas','payment',p_datos->>'metodo_pago'))::text);
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_actor::text||p_tipo||p_solicitud::text,0));
  if p_tipo='order' then
    select id,huella_solicitud into v_id,v_old_hash from public.pedidos where usuario_id=p_actor and solicitud_id=p_solicitud;
  else
    select id,huella_solicitud into v_id,v_old_hash from public.cotizaciones where usuario_id=p_actor and solicitud_id=p_solicitud;
  end if;
  if v_id is not null then
    if v_old_hash is distinct from v_hash then raise exception 'La solicitud ya fue utilizada con otros datos' using errcode='23505'; end if;
    return case when p_tipo='order' then public.neifit_pedido_json(v_id) else public.neifit_cotizacion_json(v_id) end;
  end if;
  if p_tipo='order' then
    if length(btrim(coalesce(p_datos->>'direccion',''))) not between 5 and 300 then
      raise exception 'Dirección de entrega inválida' using errcode='22023'; end if;
    v_payment:=coalesce(p_datos->>'metodo_pago','contraentrega');
    if v_payment not in ('contraentrega','transferencia') then
      raise exception 'Este medio de pago todavía no está habilitado' using errcode='22023'; end if;
    select costo_envio into v_shipping from public.configuracion_empresa where registro_unico;
    if v_shipping is null then raise exception 'Falta configurar el costo de domicilio' using errcode='22023'; end if;
  end if;
  -- Mismo orden de bloqueos para pedidos concurrentes y cambios de inventario.
  for v_product in select p.* from public.productos p where p.id in (
      select (i->>'producto_id')::uuid from jsonb_array_elements(v_items) i
    ) order by p.id for update of p loop
    v_locked:=v_locked+1;
    if not v_product.activo or not v_product.disponible or not exists(
      select 1 from public.categorias where id=v_product.categoria_id and activo) then
      raise exception 'Producto no disponible: %',v_product.nombre using errcode='P0001'; end if;
    select (i->>'cantidad')::integer as cantidad into v_item from jsonb_array_elements(v_items) i where (i->>'producto_id')::uuid=v_product.id;
    if p_tipo='order' and v_product.existencias<v_item.cantidad then
      raise exception 'Stock insuficiente: %',v_product.nombre using errcode='P0001'; end if;
    v_total:=v_total+v_product.precio*v_item.cantidad;
  end loop;
  if v_locked<>jsonb_array_length(v_items) then
    raise exception 'Uno o más productos ya no existen. Actualiza el catálogo.' using errcode='22023'; end if;
  if p_tipo='order' then
    insert into public.pedidos(usuario_id,nombre_cliente,telefono_cliente,correo_cliente,direccion,metodo_pago,estado_pago,
      subtotal,costo_envio,notas,solicitud_id,huella_solicitud,existencias_descontadas)
    values(p_actor,btrim(p_datos->>'nombre_cliente'),btrim(p_datos->>'telefono_cliente'),p_datos->>'correo_cliente',btrim(p_datos->>'direccion'),
      v_payment,'pendiente',v_total,v_shipping,p_datos->>'notas',p_solicitud,v_hash,true) returning id into v_id;
    insert into public.elementos_pedido(pedido_id,producto_id,nombre_producto,cantidad,precio_unitario)
    select v_id,p.id,p.nombre,(i->>'cantidad')::integer,p.precio
    from jsonb_array_elements(v_items) i join public.productos p on p.id=(i->>'producto_id')::uuid;
    update public.productos p set existencias=p.existencias-(i->>'cantidad')::integer
      from jsonb_array_elements(v_items) i where p.id=(i->>'producto_id')::uuid;
    insert into public.seguimiento_pedidos(pedido_id,estado,mensaje,actualizado_por)
      values(v_id,'recibido','Pedido registrado. Pago pendiente de confirmación.',p_actor);
    return public.neifit_pedido_json(v_id);
  else
    insert into public.cotizaciones(usuario_id,nombre_cliente,telefono_cliente,correo_cliente,notas,solicitud_id,huella_solicitud)
    values(p_actor,btrim(p_datos->>'nombre_cliente'),btrim(p_datos->>'telefono_cliente'),p_datos->>'correo_cliente',p_datos->>'notas',p_solicitud,v_hash)
    returning id into v_id;
    insert into public.elementos_cotizacion(cotizacion_id,producto_id,nombre_producto,cantidad,precio_referencia)
    select v_id,p.id,p.nombre,(i->>'cantidad')::integer,p.precio
    from jsonb_array_elements(v_items) i join public.productos p on p.id=(i->>'producto_id')::uuid;
    return public.neifit_cotizacion_json(v_id);
  end if;
end;
$$;

create or replace function public.neifit_leer_pedidos(p_actor uuid,p_id uuid default null,p_seguimiento text default null)
returns jsonb language sql stable security definer set search_path='' as $$
 select coalesce(jsonb_agg(public.neifit_pedido_json(o.id) order by o.creado_en desc),'[]'::jsonb)
 from public.pedidos o where (p_id is null or o.id=p_id)
   and (p_seguimiento is null or upper(o.numero_pedido)=upper(btrim(p_seguimiento))) and (
     public.neifit_actor_puede(p_actor,'orders.manage')
     or o.usuario_id=p_actor and public.neifit_actor_puede(p_actor,'orders.read_own')
     or o.usuario_mensajero_asignado_id=p_actor and public.neifit_actor_puede(p_actor,'delivery.read_assigned'));
$$;

create or replace function public.neifit_leer_cotizaciones(p_actor uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce(jsonb_agg(public.neifit_cotizacion_json(q.id) order by q.creado_en desc),'[]'::jsonb)
 from public.cotizaciones q where public.neifit_actor_puede(p_actor,'quotes.manage')
   or q.usuario_id=p_actor and public.neifit_actor_puede(p_actor,'quotes.read_own');
$$;

create or replace function public.neifit_actualizar_pedido(p_actor uuid,p_id uuid,p_estado text,p_mensaje text default '')
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_order public.pedidos%rowtype; v_permission text; v_item record; v_manage boolean;
begin
  select * into v_order from public.pedidos where id=p_id for update;
  v_manage:=public.neifit_actor_puede(p_actor,'orders.manage');
  if not found or not (v_manage or (v_order.usuario_mensajero_asignado_id is not null and v_order.usuario_mensajero_asignado_id=p_actor and public.neifit_actor_puede(p_actor,'delivery.read_assigned'))) then
    raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
  if p_estado is null or p_estado not in ('recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado') then
    raise exception 'Estado inválido' using errcode='22023'; end if;
  if not v_manage then
    v_permission:=case p_estado when 'en_ruta' then 'delivery.start'
      when 'entregado' then 'delivery.complete' when 'novedad' then 'delivery.issue' else null end;
    if v_permission is null or not public.neifit_actor_puede(p_actor,v_permission) then
      raise exception 'Acción de entrega no permitida' using errcode='42501'; end if;
    if p_estado='novedad' and v_order.estado_pedido not in ('en_preparacion','empacado','despachado','en_ruta') then
      raise exception 'La entrega todavía no permite registrar novedades' using errcode='P0001'; end if;
  end if;
  if v_order.estado_pedido=p_estado then return public.neifit_pedido_json(p_id); end if;
  if v_order.estado_pedido in ('entregado','cancelado') or not (
    v_order.estado_pedido='recibido' and p_estado in ('en_preparacion','novedad','cancelado')
    or v_order.estado_pedido='confirmado' and p_estado in ('en_preparacion','novedad','cancelado')
    or v_order.estado_pedido='en_preparacion' and p_estado in ('en_ruta','novedad','cancelado')
    or v_order.estado_pedido='empacado' and p_estado in ('en_ruta','novedad','cancelado')
    or v_order.estado_pedido='despachado' and p_estado in ('en_ruta','novedad','cancelado')
    or v_order.estado_pedido='en_ruta' and p_estado in ('entregado','novedad')
    or v_order.estado_pedido='novedad' and v_manage and p_estado in ('en_preparacion','en_ruta','cancelado')
  ) then raise exception 'Transición de estado no permitida' using errcode='P0001'; end if;
  if p_estado in ('en_ruta','entregado') and v_order.usuario_mensajero_asignado_id is null then
    raise exception 'Asigna un mensajero antes de iniciar la ruta' using errcode='P0001'; end if;
  if p_estado='cancelado' then
    if v_order.estado_pago='aprobado' then raise exception 'Revisar el reembolso antes de cancelar un pedido pagado' using errcode='P0001'; end if;
    if v_order.existencias_descontadas then
      for v_item in select i.producto_id,i.cantidad from public.elementos_pedido i where i.pedido_id=p_id order by i.producto_id loop
        update public.productos set existencias=existencias+v_item.cantidad where id=v_item.producto_id;
      end loop;
    end if;
  end if;
  update public.pedidos set estado_pedido=p_estado,estado_pago=case when p_estado='cancelado' then 'cancelado' else estado_pago end,
    existencias_descontadas=case when p_estado='cancelado' then false else existencias_descontadas end where id=p_id;
  insert into public.seguimiento_pedidos(pedido_id,estado,mensaje,actualizado_por)
    values(p_id,p_estado,coalesce(nullif(btrim(p_mensaje),''),'Estado actualizado: '||p_estado),p_actor);
  return public.neifit_pedido_json(p_id);
end;
$$;

create or replace function public.neifit_asignar_mensajero(p_actor uuid,p_id uuid,p_mensajero uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_status text;
begin
 if not public.neifit_actor_puede(p_actor,'orders.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select estado_pedido into v_status from public.pedidos where id=p_id for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if v_status in ('entregado','cancelado') then raise exception 'El pedido ya está cerrado' using errcode='P0001'; end if;
 if p_mensajero is not null and not public.neifit_actor_puede(p_mensajero,'delivery.read_assigned') then
   raise exception 'El usuario no tiene permiso de mensajería' using errcode='22023'; end if;
 update public.pedidos set usuario_mensajero_asignado_id=p_mensajero where id=p_id;
 insert into public.seguimiento_pedidos(pedido_id,estado,mensaje,actualizado_por)
 values(p_id,v_status,case when p_mensajero is null then 'Asignación de mensajero retirada' else 'Mensajero asignado' end,p_actor);
 return public.neifit_pedido_json(p_id);
end;
$$;

create or replace function public.neifit_actualizar_cotizacion(p_actor uuid,p_id uuid,p_estado text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_status text;
begin
 if not public.neifit_actor_puede(p_actor,'quotes.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select estado into v_status from public.cotizaciones where id=p_id for update;
 if not found then raise exception 'Cotización no encontrada' using errcode='P0002'; end if;
 if p_estado is null or not (p_estado=v_status or v_status='pendiente' and p_estado in ('respondida','rechazada','cancelada')
   or v_status='respondida' and p_estado in ('aceptada','rechazada','cancelada')) then
   raise exception 'Transición de cotización no permitida' using errcode='P0001'; end if;
 update public.cotizaciones set estado=p_estado where id=p_id;
 return public.neifit_cotizacion_json(p_id);
end;
$$;

create or replace function public.neifit_guardar_producto(p_actor uuid,p_datos jsonb,p_id uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_id uuid; v_product public.productos%rowtype;
begin
 if not public.neifit_actor_puede(p_actor,'products.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 if p_id is null then
   insert into public.productos(categoria_id,nombre,identificador_url,descripcion,ingredientes,alergenos,precio,existencias,activo,disponible,url_imagen,destacado)
   values((p_datos->>'categoria_id')::uuid,btrim(p_datos->>'nombre'),p_datos->>'identificador_url',coalesce(p_datos->>'descripcion',''),
     p_datos->>'ingredientes',p_datos->>'alergenos',(p_datos->>'precio')::numeric,coalesce((p_datos->>'existencias')::integer,0),
     coalesce((p_datos->>'activo')::boolean,true),coalesce((p_datos->>'disponible')::boolean,true),p_datos->>'url_imagen',coalesce((p_datos->>'destacado')::boolean,false))
   returning id into v_id;
 else
   select * into v_product from public.productos where id=p_id for update;
   if not found then raise exception 'Producto no encontrado' using errcode='P0002'; end if;
   if p_datos?'existencias' and (not p_datos?'expected_updated_at' or
     (p_datos->>'expected_updated_at')::timestamptz is distinct from v_product.actualizado_en) then
     raise exception 'El inventario cambió desde que abriste el producto. Recarga antes de guardar.' using errcode='P0001'; end if;
   -- El bloqueo serializa cambios de existencias con creación y cancelación de pedidos.
   update public.productos set
     categoria_id=case when p_datos?'categoria_id' then (p_datos->>'categoria_id')::uuid else categoria_id end,
     nombre=case when p_datos?'nombre' then btrim(p_datos->>'nombre') else nombre end,
     identificador_url=case when p_datos?'identificador_url' then p_datos->>'identificador_url' else identificador_url end,
     descripcion=case when p_datos?'descripcion' then coalesce(p_datos->>'descripcion','') else descripcion end,
     ingredientes=case when p_datos?'ingredientes' then p_datos->>'ingredientes' else ingredientes end,
     alergenos=case when p_datos?'alergenos' then p_datos->>'alergenos' else alergenos end,
     precio=case when p_datos?'precio' then (p_datos->>'precio')::numeric else precio end,
     existencias=case when p_datos?'existencias' then (p_datos->>'existencias')::integer else existencias end,
     activo=case when p_datos?'activo' then (p_datos->>'activo')::boolean else activo end,
     disponible=case when p_datos?'disponible' then (p_datos->>'disponible')::boolean else disponible end,
     url_imagen=case when p_datos?'url_imagen' then p_datos->>'url_imagen' else url_imagen end,
     destacado=case when p_datos?'destacado' then (p_datos->>'destacado')::boolean else destacado end
   where id=p_id;
   v_id:=p_id;
 end if;
 return public.neifit_producto_json(v_id);
end;
$$;

-- Revocar también los privilegios predeterminados de Supabase en TODAS las funciones nuevas.
do $$
declare signature text;
begin
 foreach signature in array array[
  'neifit_actor_puede(uuid,text)','neifit_producto_json(uuid)','neifit_pedido_json(uuid)','neifit_cotizacion_json(uuid)',
  'neifit_crear_documento(uuid,text,uuid,jsonb)','neifit_leer_pedidos(uuid,uuid,text)','neifit_leer_cotizaciones(uuid)',
  'neifit_actualizar_pedido(uuid,uuid,text,text)','neifit_asignar_mensajero(uuid,uuid,uuid)',
  'neifit_actualizar_cotizacion(uuid,uuid,text)','neifit_guardar_producto(uuid,jsonb,uuid)'
 ] loop
   execute 'revoke all on function public.'||signature||' from public,anon,authenticated';
   execute 'grant execute on function public.'||signature||' to service_role';
 end loop;
end;
$$;
notify pgrst,'reload schema';


-- ==================== migrations/0006_perfil_direcciones.sql ====================
-- Ejecutar después de 0005. No modifica pedidos ni datos existentes.
create table if not exists public.direcciones_cliente (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.perfiles(id) on delete cascade,
  etiqueta text not null check(length(trim(etiqueta)) between 2 and 50),
  direccion text not null check(length(trim(direccion)) between 5 and 300),
  ciudad text not null check(length(trim(ciudad)) between 3 and 100),
  destinatario text not null check(length(trim(destinatario)) between 3 and 100),
  telefono text not null check(length(trim(telefono)) between 7 and 30),
  notas text not null default '' check(length(notas)<=500),
  creado_en timestamptz not null default now()
);
create index if not exists customer_addresses_owner on public.direcciones_cliente(usuario_id);
alter table public.direcciones_cliente enable row level security;
revoke all on public.direcciones_cliente from public, anon, authenticated;
grant select on public.direcciones_cliente to authenticated;
grant select,insert,update,delete on public.direcciones_cliente to service_role;
drop policy if exists addresses_read_self on public.direcciones_cliente;
create policy addresses_read_self on public.direcciones_cliente for select to authenticated
using(usuario_id=(select auth.uid()) and public.neifit_tiene_permiso('profile.read'));
notify pgrst,'reload schema';


-- ==================== migrations/0007_cotizaciones_avisos_cobros.sql ====================
-- Después de 0006. Avisos internos y cobros manuales auditados; sin pasarela.
-- Excluir escenarios simulados del indicador de ingresos sin borrar su historial.
create or replace function public.neifit_pedido_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(o) - 'huella_solicitud' || jsonb_build_object(
   'is_simulated',exists(select 1 from public.transacciones_pago t where t.pedido_id=o.id and (t.proveedor='simulacion_consultas' or t.respuesta_cruda->>'simulated'='true')),
   'assigned_delivery_name',p.nombre_completo,
   'items',coalesce((select jsonb_agg(to_jsonb(i) order by i.id) from public.elementos_pedido i where i.pedido_id=o.id),'[]'::jsonb),
   'tracking_history',coalesce((select jsonb_agg(jsonb_build_object('estado',t.estado,'mensaje',t.mensaje,'timestamp',t.creado_en) order by t.creado_en,t.id)
     from public.seguimiento_pedidos t where t.pedido_id=o.id),'[]'::jsonb))
 from public.pedidos o left join public.perfiles p on p.id=o.usuario_mensajero_asignado_id where o.id=p_id;
$$;
revoke all on function public.neifit_pedido_json(uuid) from public,anon,authenticated;
grant execute on function public.neifit_pedido_json(uuid) to service_role;
alter table public.cotizaciones add column if not exists total_ofrecido numeric(12,2) check(total_ofrecido>0);
alter table public.cotizaciones add column if not exists condiciones_oferta text;
alter table public.cotizaciones add column if not exists oferta_valida_hasta timestamptz;
alter table public.cotizaciones add column if not exists respondida_en timestamptz;
alter table public.cotizaciones add column if not exists respondida_por uuid references public.perfiles(id);
create table if not exists public.notificaciones (
 id uuid primary key default gen_random_uuid(),
 usuario_id uuid not null references public.perfiles(id) on delete cascade,
 titulo text not null, mensaje text not null, enlace text not null,
 creado_en timestamptz not null default now(), leido_en timestamptz
);
create index if not exists notifications_owner_date on public.notificaciones(usuario_id,creado_en desc);
alter table public.notificaciones enable row level security;
revoke all on public.notificaciones from public,anon,authenticated;
grant select on public.notificaciones to authenticated;
grant select,insert,update on public.notificaciones to service_role;
drop policy if exists notifications_read_self on public.notificaciones;
create policy notifications_read_self on public.notificaciones for select to authenticated using(usuario_id=(select auth.uid()));

create or replace function public.neifit_aviso_documento() returns trigger
language plpgsql security definer set search_path='' as $$
declare v_number text; v_link text; v_title text;
begin
 if tg_table_name='pedidos' then
   v_number:=new.numero_pedido; v_link:='/mis-pedidos';
   if tg_op='INSERT' then v_title:='Pedido registrado';
   elsif new.estado_pedido is distinct from old.estado_pedido then v_title:='Estado del pedido: '||new.estado_pedido;
   elsif new.estado_pago is distinct from old.estado_pago then v_title:='Estado del pago: '||new.estado_pago;
   else return new; end if;
 else
   v_number:=new.numero_cotizacion; v_link:='/mis-cotizaciones';
   if tg_op='INSERT' then v_title:='Cotización registrada';
   elsif new.estado is distinct from old.estado or new.respondida_en is distinct from old.respondida_en then v_title:='Cotización: '||new.estado;
   else return new; end if;
 end if;
 insert into public.notificaciones(usuario_id,titulo,mensaje,enlace) values(new.usuario_id,v_title,v_number,v_link);
 insert into public.notificaciones(usuario_id,titulo,mensaje,enlace)
 select p.id,v_title,v_number,case when tg_table_name='pedidos' then '/admin?modulo=pedidos' else '/admin?modulo=cotizaciones' end
 from public.perfiles p where p.id<>new.usuario_id and public.neifit_actor_puede(p.id,case when tg_table_name='pedidos' then 'orders.manage' else 'quotes.manage' end);
 return new;
end;
$$;
drop trigger if exists order_notice on public.pedidos;
create trigger order_notice after insert or update on public.pedidos for each row execute function public.neifit_aviso_documento();
drop trigger if exists quote_notice on public.cotizaciones;
create trigger quote_notice after insert or update on public.cotizaciones for each row execute function public.neifit_aviso_documento();

create or replace function public.neifit_responder_cotizacion(p_actor uuid,p_id uuid,p_total numeric,p_condiciones text,p_valida_hasta timestamptz)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_status text;
begin
 if not public.neifit_actor_puede(p_actor,'quotes.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select estado into v_status from public.cotizaciones where id=p_id for update;
 if not found then raise exception 'Cotización no encontrada' using errcode='P0002'; end if;
 if v_status not in ('pendiente','respondida') then raise exception 'La cotización ya está cerrada' using errcode='P0001'; end if;
 if p_total is null or p_total<=0 or p_total>9999999999.99 or p_total::text in ('NaN','Infinity','-Infinity')
 or length(trim(coalesce(p_condiciones,''))) not between 10 and 3000 or p_valida_hasta is null or p_valida_hasta<=now() then
   raise exception 'Indica precio total, condiciones y vigencia futura' using errcode='22023'; end if;
 update public.cotizaciones set total_ofrecido=p_total,condiciones_oferta=trim(p_condiciones),oferta_valida_hasta=p_valida_hasta,
 respondida_en=clock_timestamp(),respondida_por=p_actor,estado='respondida' where id=p_id;
 insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles) values(p_actor,'quote_response',p_id::text,jsonb_build_object('total',p_total,'valid_until',p_valida_hasta));
 return public.neifit_cotizacion_json(p_id);
end;
$$;

create or replace function public.neifit_confirmar_efectivo(p_actor uuid,p_id uuid,p_importe numeric,p_referencia text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_order public.pedidos%rowtype;
begin
 if not exists(select 1 from public.perfiles where id=p_actor and rol='admin') then raise exception 'Administrador requerido' using errcode='42501'; end if;
 select * into v_order from public.pedidos where id=p_id for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if v_order.metodo_pago<>'contraentrega' or v_order.estado_pedido<>'entregado' or v_order.estado_pago not in ('pendiente','aprobado') then
 raise exception 'Solo se registra efectivo de pedidos contraentrega entregados' using errcode='P0001'; end if;
 if p_importe is distinct from v_order.total or length(trim(coalesce(p_referencia,''))) not between 3 and 200 then
 raise exception 'El importe debe coincidir con el pedido e incluir referencia del recibo' using errcode='22023'; end if;
 if v_order.estado_pago='aprobado' then
   if exists(select 1 from public.transacciones_pago where pedido_id=p_id and proveedor='contraentrega_manual') then return public.neifit_pedido_json(p_id); end if;
   raise exception 'El pedido ya tiene otro pago aprobado' using errcode='P0001';
 end if;
 insert into public.transacciones_pago(pedido_id,proveedor,referencia_proveedor,importe,moneda,estado,respuesta_cruda)
 values(p_id,'contraentrega_manual',p_id::text,p_importe,'COP','aprobado',jsonb_build_object('recorded_by',p_actor,'receipt',trim(p_referencia)));
 update public.pedidos set estado_pago='aprobado' where id=p_id;
 insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles) values(p_actor,'cash_received',p_id::text,jsonb_build_object('importe',p_importe,'receipt',trim(p_referencia)));
 return public.neifit_pedido_json(p_id);
end;
$$;
revoke all on function public.neifit_aviso_documento(),public.neifit_responder_cotizacion(uuid,uuid,numeric,text,timestamptz),public.neifit_confirmar_efectivo(uuid,uuid,numeric,text) from public,anon,authenticated;
grant execute on function public.neifit_responder_cotizacion(uuid,uuid,numeric,text,timestamptz),public.neifit_confirmar_efectivo(uuid,uuid,numeric,text) to service_role;
notify pgrst,'reload schema';


commit;

-- Resultado final: 21 tablas y rowsecurity=true en todas.
select tablename, rowsecurity from pg_tables where schemaname='public'
and tablename = any(array['perfiles','categorias','productos','carritos','elementos_carrito','pedidos','elementos_pedido','cotizaciones','elementos_cotizacion','seguimiento_pedidos','transacciones_pago','contenido_sitio','configuracion_empresa','valores_empresa','permisos','limites_permisos_rol','permisos_rol','auditoria_acceso','roles_acceso','direcciones_cliente','notificaciones'])
order by tablename;





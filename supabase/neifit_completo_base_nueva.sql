-- NEIFIT: INSTALADOR COMPLETO PARA UN PROYECTO SUPABASE NUEVO.
-- Incluye esquema inicial y migraciones 0002, 0003, 0004, 0005, 0006 y 0007.
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
    and tablename = any(array['profiles','categories','products','carts','cart_items','orders','order_items','quotes','quote_items','order_tracking','payment_transactions','site_content','company_settings','company_values','permissions','role_permission_limits','role_permissions','access_audit','access_roles','customer_addresses','notifications'])) then
    raise exception 'Ya existen tablas de Neifit. Utiliza un proyecto nuevo o revisa las migraciones pendientes. No se ha borrado ningún dato.';
  end if;
end;
$$;


-- ==================== neifit_inicial.sql ====================
-- NEIFIT: ejecutar completo en SQL Editor de un proyecto Supabase NUEVO.
-- No ejecutar sobre tablas existentes con otra estructura.
-- Sin productos/precios/stock ficticios. Las escrituras comerciales son del backend.

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default '',
  email text,
  phone text,
  role text not null default 'cliente' check (role in ('admin','mensajeria','cliente')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.categories (
  id uuid primary key default gen_random_uuid(),
  name text not null check (btrim(name) <> ''),
  slug text not null unique,
  description text not null default '',
  image text,
  is_active boolean not null default true
);

create table public.products (
  id uuid primary key default gen_random_uuid(),
  category_id uuid not null references public.categories(id),
  name text not null check (btrim(name) <> ''),
  slug text not null unique,
  description text not null default '',
  ingredients text,
  allergens text,
  price numeric(12,2) not null check (price > 0),
  stock integer not null default 0 check (stock >= 0),
  is_active boolean not null default true,
  is_available boolean not null default true,
  image_url text,
  featured boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- Disponibilidad efectiva: is_active AND is_available AND stock > 0.

create table public.carts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id),
  status text not null default 'activo' check (status in ('activo','convertido','abandonado')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index carts_one_active_per_user on public.carts(user_id) where status = 'activo';
create table public.cart_items (
  id uuid primary key default gen_random_uuid(),
  cart_id uuid not null references public.carts(id) on delete cascade,
  product_id uuid not null references public.products(id),
  quantity integer not null check (quantity > 0),
  unit_price numeric(12,2) not null check (unit_price > 0),
  subtotal numeric(14,2) generated always as (quantity * unit_price) stored,
  unique(cart_id, product_id)
);

create table public.orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id),
  order_number text not null unique default ('NF-' || gen_random_uuid()::text),
  customer_name text not null,
  customer_phone text not null,
  customer_email text,
  address text not null,
  order_status text not null default 'recibido' check (order_status in
    ('recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado')),
  payment_status text not null default 'pendiente' check (payment_status in
    ('pendiente','aprobado','rechazado','reembolsado','cancelado')),
  payment_method text,
  subtotal numeric(14,2) not null check (subtotal >= 0),
  shipping_cost numeric(12,2) not null default 0 check (shipping_cost >= 0),
  total numeric(14,2) generated always as (subtotal + shipping_cost) stored,
  notes text,
  assigned_delivery_user_id uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  product_id uuid not null references public.products(id),
  product_name text not null,
  quantity integer not null check (quantity > 0),
  unit_price numeric(12,2) not null check (unit_price > 0),
  subtotal numeric(14,2) generated always as (quantity * unit_price) stored,
  unique(order_id, product_id)
);

create table public.quotes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id),
  quote_number text not null unique default ('COT-' || gen_random_uuid()::text),
  status text not null default 'pendiente' check (status in ('pendiente','respondida','aceptada','rechazada','cancelada')),
  customer_name text not null,
  customer_phone text not null,
  customer_email text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.quote_items (
  id uuid primary key default gen_random_uuid(),
  quote_id uuid not null references public.quotes(id) on delete cascade,
  product_id uuid not null references public.products(id),
  quantity integer not null check (quantity > 0),
  reference_price numeric(12,2) not null check (reference_price > 0),
  unique(quote_id, product_id)
);
create table public.order_tracking (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  status text not null check (status in
    ('recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado')),
  message text not null default '',
  updated_by uuid references public.profiles(id),
  created_at timestamptz not null default now()
);
create table public.payment_transactions (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id),
  provider text not null,
  provider_reference text not null,
  amount numeric(14,2) not null check (amount > 0),
  currency text not null default 'COP' check (currency = 'COP'),
  status text not null default 'pendiente' check (status in
    ('pendiente','aprobado','rechazado','reembolsado','cancelado')),
  raw_response jsonb,
  created_at timestamptz not null default now(),
  unique(provider, provider_reference)
);

create table public.site_content (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  title text,
  body text not null check (btrim(body) <> ''),
  is_published boolean not null default false,
  updated_by uuid references public.profiles(id),
  updated_at timestamptz not null default now()
);
create table public.company_settings (
  id uuid primary key default gen_random_uuid(),
  singleton boolean not null default true unique check (singleton),
  business_name text not null default 'Neifit',
  phone_public text,
  whatsapp_number text check (whatsapp_number ~ '^[1-9][0-9]{7,14}$'),
  address text,
  city text,
  opening_hours jsonb,
  map_url text check (map_url is null or map_url ~ '^https://'),
  logo_url text check (logo_url is null or logo_url ~ '^https://'),
  updated_at timestamptz not null default now()
);
create table public.company_values (
  id uuid primary key default gen_random_uuid(),
  title text not null unique check (btrim(title) <> ''),
  description text not null default '',
  sort_order integer not null default 0 check (sort_order >= 0),
  is_published boolean not null default false
);

create index products_category_idx on public.products(category_id);
create index orders_user_idx on public.orders(user_id);
create index orders_status_idx on public.orders(order_status);
create index orders_delivery_idx on public.orders(assigned_delivery_user_id);
create index order_items_order_idx on public.order_items(order_id);
create index quotes_user_idx on public.quotes(user_id);
create index quote_items_quote_idx on public.quote_items(quote_id);
create index tracking_order_idx on public.order_tracking(order_id, created_at);
create index payments_order_idx on public.payment_transactions(order_id);

create function public.neifit_set_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
do $$
declare table_name text;
begin
  foreach table_name in array array['profiles','products','carts','orders','quotes','site_content','company_settings'] loop
    execute format('create trigger neifit_updated_at before update on public.%I for each row execute function public.neifit_set_updated_at()', table_name);
  end loop;
end;
$$;

-- Ignora cualquier rol enviado en los metadatos del registro.
create function public.neifit_handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles(id, email, full_name, phone, role)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'full_name',''),
          new.raw_user_meta_data->>'phone', 'cliente');
  return new;
end;
$$;
create trigger neifit_auth_user_created after insert on auth.users
for each row execute function public.neifit_handle_new_user();
-- Incluye usuarios que se hubieran registrado antes de ejecutar este archivo.
insert into public.profiles(id, email, full_name, phone)
select id, email, coalesce(raw_user_meta_data->>'full_name',''), raw_user_meta_data->>'phone'
from auth.users on conflict (id) do nothing;

-- RLS y privilegios explícitos. El navegador no modifica reglas comerciales.
do $$
declare table_name text;
begin
  foreach table_name in array array['profiles','categories','products','carts','cart_items',
    'orders','order_items','quotes','quote_items','order_tracking','payment_transactions',
    'site_content','company_settings','company_values'] loop
    execute format('alter table public.%I enable row level security', table_name);
    execute format('revoke all on table public.%I from anon, authenticated', table_name);
    execute format('grant all on table public.%I to service_role', table_name);
  end loop;
end;
$$;
grant usage on schema public to anon, authenticated, service_role;
grant select on public.categories, public.site_content,
  public.company_settings, public.company_values to anon, authenticated;
grant select on public.products to authenticated;
grant select on public.profiles, public.carts, public.cart_items, public.orders,
  public.order_items, public.quotes, public.quote_items, public.order_tracking to authenticated;
-- El usuario puede corregir su nombre/teléfono, nunca role, id ni email.
grant update(full_name, phone) on public.profiles to authenticated;
create policy profiles_read_self on public.profiles for select to authenticated using (id = (select auth.uid()));
create policy profiles_update_self on public.profiles for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));
create policy categories_public on public.categories for select to anon, authenticated using (is_active);
create policy products_public on public.products for select to authenticated
  using (is_active and exists (select 1 from public.categories c where c.id = category_id and c.is_active));
create policy content_public on public.site_content for select to anon, authenticated using (is_published);
create policy settings_public on public.company_settings for select to anon, authenticated using (true);
create policy values_public on public.company_values for select to anon, authenticated using (is_published);
create policy carts_read_self on public.carts for select to authenticated using (user_id = (select auth.uid()));
create policy cart_items_read_self on public.cart_items for select to authenticated
  using (exists (select 1 from public.carts c where c.id = cart_id and c.user_id = (select auth.uid())));
create policy orders_read_self on public.orders for select to authenticated using (user_id = (select auth.uid()));
create policy order_items_read_self on public.order_items for select to authenticated
  using (exists (select 1 from public.orders o where o.id = order_id and o.user_id = (select auth.uid())));
create policy quotes_read_self on public.quotes for select to authenticated using (user_id = (select auth.uid()));
create policy quote_items_read_self on public.quote_items for select to authenticated
  using (exists (select 1 from public.quotes q where q.id = quote_id and q.user_id = (select auth.uid())));
create policy tracking_read_self on public.order_tracking for select to authenticated
  using (exists (select 1 from public.orders o where o.id = order_id and o.user_id = (select auth.uid())));
-- Sin acceso directo a payment_transactions (contiene respuesta privada del proveedor).
-- Admin/mensajería operan a través de FastAPI, que debe verificar rol/asignación.
revoke all on function public.neifit_handle_new_user() from public, anon, authenticated;
revoke all on function public.neifit_set_updated_at() from public, anon, authenticated;

-- Storage: imágenes públicas de productos; evidencias privadas solo vía backend.
insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values ('products','products',true,5242880,array['image/jpeg','image/png','image/webp']),
       ('evidence','evidence',false,5242880,array['image/jpeg','image/png','image/webp','application/pdf'])
on conflict (id) do nothing;
-- No se conceden cargas/borrados al navegador. Usar backend o Dashboard.

insert into public.categories(name, slug, description) values
 ('Postres','postres','Postres de la selección Neifit.'),
 ('Snacks','snacks','Snacks de la selección Neifit.'),
 ('Bebidas','bebidas','Bebidas de la selección Neifit.');
insert into public.company_settings(business_name, phone_public, whatsapp_number, address, city, opening_hours)
values ('Neifit','+57 3127827020','573127827020','CR 28B # 38F - 56','Medellín, Antioquia, Colombia',
 '{"timezone":"America/Bogota","monday":"09:00-18:00","tuesday":"09:00-18:00","wednesday":"09:00-18:00","thursday":"09:00-18:00","friday":"09:00-18:00","saturday":null,"sunday":null}'::jsonb);
insert into public.site_content(key, title, body, is_published) values
 ('hero_title','Portada','Sabores naturales que cuentan historias',true),
 ('hero_description','Presentación','Postres, snacks y bebidas con el sabor de nuestras raíces.',true),
 ('about_us','Quiénes somos','En Neifit reunimos sabores tradicionales, frutas y opciones para acompañar distintos momentos del día. Queremos que comprar sea una experiencia cercana y sencilla.',true),
 ('mission','Misión','Ofrecer una selección de postres, snacks y bebidas con atención cálida, información transparente y respeto por los sabores regionales.',true),
 ('vision','Visión','Ser una marca colombiana reconocida por conectar tradición, variedad y una experiencia de compra confiable.',true);
insert into public.company_values(title, sort_order, is_published) values
 ('Calidad',1,true),('Transparencia',2,true),('Cercanía',3,true),
 ('Innovación',4,true),('Responsabilidad',5,true),('Tradición',6,true);

-- Comprobación: 14 tablas con RLS, 3 categorías, 5 contenidos, 6 valores.
select tablename, rowsecurity from pg_tables where schemaname = 'public'
and tablename in ('profiles','categories','products','carts','cart_items','orders','order_items',
 'quotes','quote_items','order_tracking','payment_transactions','site_content','company_settings','company_values')
order by tablename;


-- ==================== migrations/0002_catalogo_autenticado.sql ====================
-- Ejecutar una vez en SQL Editor si ya instalaste neifit_inicial.sql.
-- No reinstalar el esquema ni borrar datos.
-- La landing recibe una muestra controlada desde FastAPI /site/featured-products.
revoke select on table public.products from anon;
alter policy products_public on public.products to authenticated;

select has_table_privilege('anon','public.products','SELECT') as anon_puede_leer_catalogo;
-- Debe devolver false. El contenido institucional sigue siendo público.


-- ==================== migrations/0003_roles_permisos.sql ====================
-- Ejecutar después del esquema inicial y 0002_catalogo_autenticado.sql.
-- No borra datos. Tras aplicarlo, activar RBAC_DATABASE_ENABLED=true en backend.
create table public.permissions (
  code text primary key,
  description text not null
);
create table public.role_permission_limits (
  role text not null check (role in ('cliente','mensajeria','admin')),
  permission_code text not null references public.permissions(code),
  primary key(role, permission_code)
);
create table public.role_permissions (
  role text not null,
  permission_code text not null,
  primary key(role, permission_code),
  foreign key(role, permission_code) references public.role_permission_limits(role, permission_code)
);
create table public.access_audit (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid not null references public.profiles(id),
  action text not null,
  target text not null,
  details jsonb not null,
  created_at timestamptz not null default now()
);

insert into public.permissions(code,description) values
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
insert into public.role_permission_limits(role,permission_code) values
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
insert into public.role_permissions select * from public.role_permission_limits;

alter table public.permissions enable row level security;
alter table public.role_permission_limits enable row level security;
alter table public.role_permissions enable row level security;
alter table public.access_audit enable row level security;
revoke all on public.permissions, public.role_permission_limits, public.role_permissions, public.access_audit from anon, authenticated, service_role;
grant select on public.permissions, public.role_permissions to authenticated;
grant select on public.permissions, public.role_permission_limits, public.role_permissions, public.access_audit to service_role;
create policy permission_names on public.permissions for select to authenticated using (true);
create policy own_role_permissions on public.role_permissions for select to authenticated
using (role = (select p.role from public.profiles p where p.id = (select auth.uid())));

create function public.neifit_has_permission(p_code text) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles p where p.id = auth.uid()
    and (p.role = 'admin' and exists(select 1 from public.permissions where code = p_code)
      or exists(select 1 from public.role_permissions rp where rp.role = p.role and rp.permission_code = p_code))
  );
$$;
revoke all on function public.neifit_has_permission(text) from public, anon;
grant execute on function public.neifit_has_permission(text) to authenticated;

-- Solo FastAPI con clave de servidor puede invocar los cambios.
-- Ambas funciones serializan cambios y vuelven a comprobar el actor en BD.
create function public.neifit_assign_role(p_actor_id uuid, p_user_id uuid, p_role text)
returns void language plpgsql security definer set search_path = '' as $$
declare previous_role text;
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.profiles where id = p_actor_id and role = 'admin') then
    raise exception 'Administrador requerido' using errcode='42501';
  end if;
  if p_actor_id = p_user_id or p_role not in ('cliente','mensajeria','admin') then
    raise exception 'Cambio de rol no permitido' using errcode='42501';
  end if;
  select role into previous_role from public.profiles where id = p_user_id for update;
  if not found then raise exception 'Usuario no encontrado' using errcode='22023'; end if;
  if previous_role = 'admin' and p_role <> 'admin'
    and (select count(*) from public.profiles where role = 'admin') <= 1 then
    raise exception 'Debe existir un administrador' using errcode='42501';
  end if;
  update public.profiles set role = p_role where id = p_user_id;
  insert into public.access_audit(actor_id,action,target,details)
  values(p_actor_id,'assign_role',p_user_id::text,jsonb_build_object('previous_role',previous_role,'role',p_role));
end;
$$;

create function public.neifit_set_role_permissions(p_actor_id uuid, p_role text, p_permissions text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.profiles where id = p_actor_id and role = 'admin')
    or p_role not in ('cliente','mensajeria') then
    raise exception 'Cambio de permisos no permitido' using errcode='42501';
  end if;
  if p_permissions is null or not ('profile.read' = any(p_permissions)) then
    raise exception 'El perfil propio es un permiso obligatorio' using errcode='42501';
  end if;
  if exists(select 1 from unnest(p_permissions) code where code is null or not exists(
    select 1 from public.role_permission_limits l where l.role = p_role and l.permission_code = code)) then
    raise exception 'Permiso fuera del alcance del rol' using errcode='42501';
  end if;
  delete from public.role_permissions where role = p_role;
  insert into public.role_permissions(role,permission_code) select p_role, code from (select distinct unnest(p_permissions) code) s;
  insert into public.access_audit(actor_id,action,target,details)
  values(p_actor_id,'set_permissions',p_role,jsonb_build_object('permissions',p_permissions));
end;
$$;
revoke all on function public.neifit_assign_role(uuid,uuid,text) from public, anon, authenticated;
revoke all on function public.neifit_set_role_permissions(uuid,text,text[]) from public, anon, authenticated;
grant execute on function public.neifit_assign_role(uuid,uuid,text), public.neifit_set_role_permissions(uuid,text,text[]) to service_role;

-- Lectura por permiso y propiedad. Mensajería recibe datos por FastAPI con
-- proyección logística; no se le concede SELECT directo de pedidos completos.
alter policy products_public on public.products using (
  is_active and public.neifit_has_permission('catalog.read')
  and exists(select 1 from public.categories c where c.id = category_id and c.is_active)
);
alter policy orders_read_self on public.orders using (user_id = (select auth.uid()) and public.neifit_has_permission('orders.read_own'));
alter policy order_items_read_self on public.order_items using (public.neifit_has_permission('orders.read_own') and exists(select 1 from public.orders o where o.id = order_id and o.user_id = (select auth.uid())));
alter policy tracking_read_self on public.order_tracking using (public.neifit_has_permission('orders.read_own') and exists(select 1 from public.orders o where o.id = order_id and o.user_id = (select auth.uid())));
alter policy quotes_read_self on public.quotes using (user_id = (select auth.uid()) and public.neifit_has_permission('quotes.read_own'));
alter policy quote_items_read_self on public.quote_items using (public.neifit_has_permission('quotes.read_own') and exists(select 1 from public.quotes q where q.id = quote_id and q.user_id = (select auth.uid())));
alter policy carts_read_self on public.carts using (user_id = (select auth.uid()) and public.neifit_has_permission('orders.create'));
alter policy cart_items_read_self on public.cart_items using (public.neifit_has_permission('orders.create') and exists(select 1 from public.carts c where c.id = cart_id and c.user_id = (select auth.uid())));

select role, count(*) as permisos from public.role_permissions group by role order by role;


-- ==================== migrations/0004_usuarios_roles_personalizados.sql ====================
-- Ejecutar después de 0003_roles_permisos.sql. No elimina usuarios ni datos.
create table public.access_roles (
  code text primary key check(code ~ '^[a-z][a-z0-9_]{2,39}$'),
  name text not null check(length(trim(name)) between 3 and 60),
  created_at timestamptz not null default now()
);
insert into public.access_roles(code,name) values
 ('admin','Administrador'),('cliente','Cliente'),('mensajeria','Mensajero / domiciliario');
alter table public.profiles drop constraint profiles_role_check;
alter table public.profiles add constraint profiles_role_fkey foreign key(role) references public.access_roles(code);
alter table public.role_permission_limits drop constraint role_permission_limits_role_check;
alter table public.role_permission_limits add constraint role_permission_limits_role_fkey foreign key(role) references public.access_roles(code);
insert into public.permissions(code,description) values ('users.manage','Gestionar usuarios y registrar mensajeros');
insert into public.role_permission_limits(role,permission_code) values ('admin','users.manage');
insert into public.role_permissions(role,permission_code) values ('admin','users.manage');
alter table public.access_roles enable row level security;
revoke all on public.access_roles from public, anon, authenticated, service_role;
grant select on public.access_roles to service_role;
create or replace function public.neifit_assign_role(p_actor_id uuid, p_user_id uuid, p_role text)
returns void language plpgsql security definer set search_path = '' as $$
declare previous_role text;
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.profiles where id = p_actor_id and role = 'admin') then
    raise exception 'Administrador requerido' using errcode='42501';
  end if;
  if p_actor_id = p_user_id or not exists(select 1 from public.access_roles where code = p_role) then
    raise exception 'Cambio de rol no permitido' using errcode='42501';
  end if;
  select role into previous_role from public.profiles where id = p_user_id for update;
  if not found then raise exception 'Usuario no encontrado' using errcode='22023'; end if;
  if previous_role = 'admin' and p_role <> 'admin'
    and (select count(*) from public.profiles where role = 'admin') <= 1 then
    raise exception 'Debe existir un administrador' using errcode='42501';
  end if;
  update public.profiles set role = p_role where id = p_user_id;
  insert into public.access_audit(actor_id,action,target,details)
  values(p_actor_id,'assign_role',p_user_id::text,jsonb_build_object('previous_role',previous_role,'role',p_role));
end;
$$;

create or replace function public.neifit_set_role_permissions(p_actor_id uuid, p_role text, p_permissions text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.profiles where id = p_actor_id and role = 'admin')
    or p_role = 'admin' or not exists(select 1 from public.access_roles where code = p_role) then
    raise exception 'Cambio de permisos no permitido' using errcode='42501';
  end if;
  if p_permissions is null or not ('profile.read' = any(p_permissions)) then
    raise exception 'El perfil propio es un permiso obligatorio' using errcode='42501';
  end if;
  if exists(select 1 from unnest(p_permissions) code where code is null or not exists(
    select 1 from public.role_permission_limits l where l.role = p_role and l.permission_code = code)) then
    raise exception 'Permiso fuera del alcance del rol' using errcode='42501';
  end if;
  delete from public.role_permissions where role = p_role;
  insert into public.role_permissions(role,permission_code) select p_role, code from (select distinct unnest(p_permissions) code) s;
  insert into public.access_audit(actor_id,action,target,details)
  values(p_actor_id,'set_permissions',p_role,jsonb_build_object('permissions',p_permissions));
end;
$$;
revoke all on function public.neifit_assign_role(uuid,uuid,text) from public, anon, authenticated;
revoke all on function public.neifit_set_role_permissions(uuid,text,text[]) from public, anon, authenticated;
grant execute on function public.neifit_assign_role(uuid,uuid,text), public.neifit_set_role_permissions(uuid,text,text[]) to service_role;


create function public.neifit_create_role(p_actor_id uuid, p_code text, p_name text, p_permissions text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform pg_catalog.pg_advisory_xact_lock(428704219);
  if not exists(select 1 from public.profiles where id = p_actor_id and role = 'admin') then
    raise exception 'Administrador requerido' using errcode='42501';
  end if;
  if p_code is null or p_code !~ '^[a-z][a-z0-9_]{2,39}$'
     or p_code in ('admin','cliente','mensajeria')
     or p_name is null or length(trim(p_name)) not between 3 and 60
     or p_permissions is null or not ('profile.read' = any(p_permissions)) then
    raise exception 'Rol o permisos inválidos' using errcode='22023';
  end if;
  if exists(select 1 from unnest(p_permissions) as requested(code) where requested.code is null
    or requested.code in ('access.manage','users.manage')
    or not exists(select 1 from public.permissions p where p.code = requested.code)) then
    raise exception 'Permisos no delegables' using errcode='42501';
  end if;
  insert into public.access_roles(code,name) values(p_code,trim(p_name));
  insert into public.role_permission_limits(role,permission_code)
    select p_code,code from public.permissions where code not in ('access.manage','users.manage');
  insert into public.role_permissions(role,permission_code)
    select p_code,code from (select distinct unnest(p_permissions) code) s;
  insert into public.access_audit(actor_id,action,target,details)
    values(p_actor_id,'create_role',p_code,jsonb_build_object('name',trim(p_name),'permissions',p_permissions));
end;
$$;
revoke all on function public.neifit_create_role(uuid,text,text,text[]) from public, anon, authenticated;
grant execute on function public.neifit_create_role(uuid,text,text,text[]) to service_role;
select code,name from public.access_roles order by name;


-- ==================== migrations/0005_servicios_comerciales.sql ====================
-- Persistencia comercial. Requiere esquema inicial y migraciones 0002-0004.
-- Ejecutable de nuevo sin borrar registros ni restablecer configuraciones.

alter table public.company_settings add column if not exists shipping_cost numeric(12,2) not null default 5000 check(shipping_cost >= 0);
alter table public.orders add column if not exists request_id uuid not null default gen_random_uuid();
alter table public.orders add column if not exists request_fingerprint text;
alter table public.orders add column if not exists stock_debited boolean not null default false;
alter table public.quotes add column if not exists request_id uuid not null default gen_random_uuid();
alter table public.quotes add column if not exists request_fingerprint text;
alter table public.quote_items add column if not exists product_name text not null default '';
update public.quote_items qi set product_name=p.name from public.products p where p.id=qi.product_id and qi.product_name='';
create unique index if not exists orders_request_once on public.orders(user_id,request_id);
create unique index if not exists quotes_request_once on public.quotes(user_id,request_id);

-- Solo servidor. El actor siempre proviene del JWT validado por FastAPI.
create or replace function public.neifit_actor_can(p_actor uuid,p_code text) returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.profiles p where p.id=p_actor and (
    p.role='admin' and exists(select 1 from public.permissions where code=p_code)
    or exists(select 1 from public.role_permissions rp where rp.role=p.role and rp.permission_code=p_code)));
$$;

create or replace function public.neifit_product_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(p) || jsonb_build_object('category_name',c.name,'category_slug',c.slug,'sales_enabled',p.is_available,
   'is_available',p.is_active and p.is_available and p.stock>0 and c.is_active)
 from public.products p join public.categories c on c.id=p.category_id where p.id=p_id;
$$;

create or replace function public.neifit_order_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(o) - 'request_fingerprint' || jsonb_build_object(
   'assigned_delivery_name',p.full_name,
   'items',coalesce((select jsonb_agg(to_jsonb(i) order by i.id) from public.order_items i where i.order_id=o.id),'[]'::jsonb),
   'tracking_history',coalesce((select jsonb_agg(jsonb_build_object('status',t.status,'message',t.message,'timestamp',t.created_at) order by t.created_at,t.id)
     from public.order_tracking t where t.order_id=o.id),'[]'::jsonb))
 from public.orders o left join public.profiles p on p.id=o.assigned_delivery_user_id where o.id=p_id;
$$;

create or replace function public.neifit_quote_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(q) - 'request_fingerprint' || jsonb_build_object(
   'items',coalesce((select jsonb_agg(to_jsonb(i) order by i.id) from public.quote_items i where i.quote_id=q.id),'[]'::jsonb))
 from public.quotes q where q.id=p_id;
$$;

create or replace function public.neifit_create_document(p_actor uuid,p_kind text,p_request uuid,p_data jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
  v_id uuid; v_old_hash text; v_hash text; v_items jsonb; v_item record;
  v_product public.products%rowtype; v_total numeric(14,2):=0; v_shipping numeric(12,2);
  v_payment text; v_locked integer:=0;
begin
  if p_kind not in ('order','quote') or p_kind is null or p_request is null then
    raise exception 'Solicitud inválida' using errcode='22023'; end if;
  if not public.neifit_actor_can(p_actor,case when p_kind='order' then 'orders.create' else 'quotes.create' end) then
    raise exception 'No tienes permiso para crear esta solicitud' using errcode='42501'; end if;
  if jsonb_typeof(p_data->'items') is distinct from 'array' or jsonb_array_length(p_data->'items') not between 1 and 100 then
    raise exception 'Incluye entre 1 y 100 productos' using errcode='22023'; end if;
  if length(btrim(coalesce(p_data->>'customer_name',''))) not between 3 and 100
    or length(btrim(coalesce(p_data->>'customer_phone',''))) not between 7 and 30 then
    raise exception 'Nombre y teléfono inválidos' using errcode='22023'; end if;
  if exists(select 1 from jsonb_array_elements(p_data->'items') i where
    jsonb_typeof(i->'quantity') is distinct from 'number' or (i->>'quantity') !~ '^[0-9]+$'
    or (i->>'quantity')::numeric not between 1 and 10000 or i->>'product_id' is null) then
    raise exception 'Productos o cantidades inválidos' using errcode='22023'; end if;
  select jsonb_agg(jsonb_build_object('product_id',id,'quantity',qty) order by id) into v_items from (
    select (i->>'product_id')::uuid as id,sum((i->>'quantity')::integer) as qty
    from jsonb_array_elements(p_data->'items') i group by (i->>'product_id')::uuid
  ) x;
  if exists(select 1 from jsonb_array_elements(v_items) i where (i->>'quantity')::integer>10000) then
    raise exception 'Cantidad máxima superada' using errcode='22023'; end if;
  -- Ignorar los precios, totales y propietario declarados por el navegador.
  v_hash:=md5((jsonb_build_object('items',v_items,'name',p_data->>'customer_name','phone',p_data->>'customer_phone',
    'email',p_data->>'customer_email','address',p_data->>'address','notes',p_data->>'notes','payment',p_data->>'payment_method'))::text);
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_actor::text||p_kind||p_request::text,0));
  if p_kind='order' then
    select id,request_fingerprint into v_id,v_old_hash from public.orders where user_id=p_actor and request_id=p_request;
  else
    select id,request_fingerprint into v_id,v_old_hash from public.quotes where user_id=p_actor and request_id=p_request;
  end if;
  if v_id is not null then
    if v_old_hash is distinct from v_hash then raise exception 'La solicitud ya fue utilizada con otros datos' using errcode='23505'; end if;
    return case when p_kind='order' then public.neifit_order_json(v_id) else public.neifit_quote_json(v_id) end;
  end if;
  if p_kind='order' then
    if length(btrim(coalesce(p_data->>'address',''))) not between 5 and 300 then
      raise exception 'Dirección de entrega inválida' using errcode='22023'; end if;
    v_payment:=coalesce(p_data->>'payment_method','contraentrega');
    if v_payment not in ('contraentrega','transferencia') then
      raise exception 'Este medio de pago todavía no está habilitado' using errcode='22023'; end if;
    select shipping_cost into v_shipping from public.company_settings where singleton;
    if v_shipping is null then raise exception 'Falta configurar el costo de domicilio' using errcode='22023'; end if;
  end if;
  -- Mismo orden de bloqueos para pedidos concurrentes y cambios de inventario.
  for v_product in select p.* from public.products p where p.id in (
      select (i->>'product_id')::uuid from jsonb_array_elements(v_items) i
    ) order by p.id for update of p loop
    v_locked:=v_locked+1;
    if not v_product.is_active or not v_product.is_available or not exists(
      select 1 from public.categories where id=v_product.category_id and is_active) then
      raise exception 'Producto no disponible: %',v_product.name using errcode='P0001'; end if;
    select (i->>'quantity')::integer as quantity into v_item from jsonb_array_elements(v_items) i where (i->>'product_id')::uuid=v_product.id;
    if p_kind='order' and v_product.stock<v_item.quantity then
      raise exception 'Stock insuficiente: %',v_product.name using errcode='P0001'; end if;
    v_total:=v_total+v_product.price*v_item.quantity;
  end loop;
  if v_locked<>jsonb_array_length(v_items) then
    raise exception 'Uno o más productos ya no existen. Actualiza el catálogo.' using errcode='22023'; end if;
  if p_kind='order' then
    insert into public.orders(user_id,customer_name,customer_phone,customer_email,address,payment_method,payment_status,
      subtotal,shipping_cost,notes,request_id,request_fingerprint,stock_debited)
    values(p_actor,btrim(p_data->>'customer_name'),btrim(p_data->>'customer_phone'),p_data->>'customer_email',btrim(p_data->>'address'),
      v_payment,'pendiente',v_total,v_shipping,p_data->>'notes',p_request,v_hash,true) returning id into v_id;
    insert into public.order_items(order_id,product_id,product_name,quantity,unit_price)
    select v_id,p.id,p.name,(i->>'quantity')::integer,p.price
    from jsonb_array_elements(v_items) i join public.products p on p.id=(i->>'product_id')::uuid;
    update public.products p set stock=p.stock-(i->>'quantity')::integer
      from jsonb_array_elements(v_items) i where p.id=(i->>'product_id')::uuid;
    insert into public.order_tracking(order_id,status,message,updated_by)
      values(v_id,'recibido','Pedido registrado. Pago pendiente de confirmación.',p_actor);
    return public.neifit_order_json(v_id);
  else
    insert into public.quotes(user_id,customer_name,customer_phone,customer_email,notes,request_id,request_fingerprint)
    values(p_actor,btrim(p_data->>'customer_name'),btrim(p_data->>'customer_phone'),p_data->>'customer_email',p_data->>'notes',p_request,v_hash)
    returning id into v_id;
    insert into public.quote_items(quote_id,product_id,product_name,quantity,reference_price)
    select v_id,p.id,p.name,(i->>'quantity')::integer,p.price
    from jsonb_array_elements(v_items) i join public.products p on p.id=(i->>'product_id')::uuid;
    return public.neifit_quote_json(v_id);
  end if;
end;
$$;

create or replace function public.neifit_read_orders(p_actor uuid,p_id uuid default null,p_tracking text default null)
returns jsonb language sql stable security definer set search_path='' as $$
 select coalesce(jsonb_agg(public.neifit_order_json(o.id) order by o.created_at desc),'[]'::jsonb)
 from public.orders o where (p_id is null or o.id=p_id)
   and (p_tracking is null or upper(o.order_number)=upper(btrim(p_tracking))) and (
     public.neifit_actor_can(p_actor,'orders.manage')
     or o.user_id=p_actor and public.neifit_actor_can(p_actor,'orders.read_own')
     or o.assigned_delivery_user_id=p_actor and public.neifit_actor_can(p_actor,'delivery.read_assigned'));
$$;

create or replace function public.neifit_read_quotes(p_actor uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce(jsonb_agg(public.neifit_quote_json(q.id) order by q.created_at desc),'[]'::jsonb)
 from public.quotes q where public.neifit_actor_can(p_actor,'quotes.manage')
   or q.user_id=p_actor and public.neifit_actor_can(p_actor,'quotes.read_own');
$$;

create or replace function public.neifit_update_order(p_actor uuid,p_id uuid,p_status text,p_message text default '')
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_order public.orders%rowtype; v_permission text; v_item record; v_manage boolean;
begin
  select * into v_order from public.orders where id=p_id for update;
  v_manage:=public.neifit_actor_can(p_actor,'orders.manage');
  if not found or not (v_manage or (v_order.assigned_delivery_user_id is not null and v_order.assigned_delivery_user_id=p_actor and public.neifit_actor_can(p_actor,'delivery.read_assigned'))) then
    raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
  if p_status is null or p_status not in ('recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado') then
    raise exception 'Estado inválido' using errcode='22023'; end if;
  if not v_manage then
    v_permission:=case p_status when 'despachado' then 'delivery.start' when 'en_ruta' then 'delivery.start'
      when 'entregado' then 'delivery.complete' when 'novedad' then 'delivery.issue' else null end;
    if v_permission is null or not public.neifit_actor_can(p_actor,v_permission) then
      raise exception 'Acción de entrega no permitida' using errcode='42501'; end if;
    if p_status='novedad' and v_order.order_status not in ('empacado','despachado','en_ruta') then
      raise exception 'La entrega todavía no permite registrar novedades' using errcode='P0001'; end if;
  end if;
  if v_order.order_status=p_status then return public.neifit_order_json(p_id); end if;
  if v_order.order_status in ('entregado','cancelado') or not (
    v_order.order_status='recibido' and p_status in ('confirmado','novedad','cancelado')
    or v_order.order_status='confirmado' and p_status in ('en_preparacion','novedad','cancelado')
    or v_order.order_status='en_preparacion' and p_status in ('empacado','novedad','cancelado')
    or v_order.order_status='empacado' and p_status in ('despachado','novedad','cancelado')
    or v_order.order_status='despachado' and p_status in ('en_ruta','novedad')
    or v_order.order_status='en_ruta' and p_status in ('entregado','novedad')
    or v_order.order_status='novedad' and v_manage and p_status in ('confirmado','en_preparacion','empacado','despachado','en_ruta','cancelado')
  ) then raise exception 'Transición de estado no permitida' using errcode='P0001'; end if;
  if p_status in ('despachado','en_ruta','entregado') and v_order.assigned_delivery_user_id is null then
    raise exception 'Asigna un mensajero antes de despachar' using errcode='P0001'; end if;
  if p_status='cancelado' then
    if v_order.payment_status='aprobado' then raise exception 'Revisar el reembolso antes de cancelar un pedido pagado' using errcode='P0001'; end if;
    if v_order.stock_debited then
      for v_item in select i.product_id,i.quantity from public.order_items i where i.order_id=p_id order by i.product_id loop
        update public.products set stock=stock+v_item.quantity where id=v_item.product_id;
      end loop;
    end if;
  end if;
  update public.orders set order_status=p_status,payment_status=case when p_status='cancelado' then 'cancelado' else payment_status end,
    stock_debited=case when p_status='cancelado' then false else stock_debited end where id=p_id;
  insert into public.order_tracking(order_id,status,message,updated_by)
    values(p_id,p_status,coalesce(nullif(btrim(p_message),''),'Estado actualizado: '||p_status),p_actor);
  return public.neifit_order_json(p_id);
end;
$$;

create or replace function public.neifit_assign_delivery(p_actor uuid,p_id uuid,p_delivery uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_status text;
begin
 if not public.neifit_actor_can(p_actor,'orders.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select order_status into v_status from public.orders where id=p_id for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if v_status in ('entregado','cancelado') then raise exception 'El pedido ya está cerrado' using errcode='P0001'; end if;
 if p_delivery is not null and not public.neifit_actor_can(p_delivery,'delivery.read_assigned') then
   raise exception 'El usuario no tiene permiso de mensajería' using errcode='22023'; end if;
 update public.orders set assigned_delivery_user_id=p_delivery where id=p_id;
 insert into public.order_tracking(order_id,status,message,updated_by)
 values(p_id,v_status,case when p_delivery is null then 'Asignación de mensajero retirada' else 'Mensajero asignado' end,p_actor);
 return public.neifit_order_json(p_id);
end;
$$;

create or replace function public.neifit_update_quote(p_actor uuid,p_id uuid,p_status text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_status text;
begin
 if not public.neifit_actor_can(p_actor,'quotes.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select status into v_status from public.quotes where id=p_id for update;
 if not found then raise exception 'Cotización no encontrada' using errcode='P0002'; end if;
 if p_status is null or not (p_status=v_status or v_status='pendiente' and p_status in ('respondida','rechazada','cancelada')
   or v_status='respondida' and p_status in ('aceptada','rechazada','cancelada')) then
   raise exception 'Transición de cotización no permitida' using errcode='P0001'; end if;
 update public.quotes set status=p_status where id=p_id;
 return public.neifit_quote_json(p_id);
end;
$$;

create or replace function public.neifit_save_product(p_actor uuid,p_data jsonb,p_id uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_id uuid; v_product public.products%rowtype;
begin
 if not public.neifit_actor_can(p_actor,'products.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 if p_id is null then
   insert into public.products(category_id,name,slug,description,ingredients,allergens,price,stock,is_active,is_available,image_url,featured)
   values((p_data->>'category_id')::uuid,btrim(p_data->>'name'),p_data->>'slug',coalesce(p_data->>'description',''),
     p_data->>'ingredients',p_data->>'allergens',(p_data->>'price')::numeric,coalesce((p_data->>'stock')::integer,0),
     coalesce((p_data->>'is_active')::boolean,true),coalesce((p_data->>'is_available')::boolean,true),p_data->>'image_url',coalesce((p_data->>'featured')::boolean,false))
   returning id into v_id;
 else
   select * into v_product from public.products where id=p_id for update;
   if not found then raise exception 'Producto no encontrado' using errcode='P0002'; end if;
   if p_data?'stock' and (not p_data?'expected_updated_at' or
     (p_data->>'expected_updated_at')::timestamptz is distinct from v_product.updated_at) then
     raise exception 'El inventario cambió desde que abriste el producto. Recarga antes de guardar.' using errcode='P0001'; end if;
   -- El bloqueo serializa cambios de stock con creación y cancelación de pedidos.
   update public.products set
     category_id=case when p_data?'category_id' then (p_data->>'category_id')::uuid else category_id end,
     name=case when p_data?'name' then btrim(p_data->>'name') else name end,
     slug=case when p_data?'slug' then p_data->>'slug' else slug end,
     description=case when p_data?'description' then coalesce(p_data->>'description','') else description end,
     ingredients=case when p_data?'ingredients' then p_data->>'ingredients' else ingredients end,
     allergens=case when p_data?'allergens' then p_data->>'allergens' else allergens end,
     price=case when p_data?'price' then (p_data->>'price')::numeric else price end,
     stock=case when p_data?'stock' then (p_data->>'stock')::integer else stock end,
     is_active=case when p_data?'is_active' then (p_data->>'is_active')::boolean else is_active end,
     is_available=case when p_data?'is_available' then (p_data->>'is_available')::boolean else is_available end,
     image_url=case when p_data?'image_url' then p_data->>'image_url' else image_url end,
     featured=case when p_data?'featured' then (p_data->>'featured')::boolean else featured end
   where id=p_id;
   v_id:=p_id;
 end if;
 return public.neifit_product_json(v_id);
end;
$$;

-- Revocar también los privilegios predeterminados de Supabase en TODAS las funciones nuevas.
do $$
declare signature text;
begin
 foreach signature in array array[
  'neifit_actor_can(uuid,text)','neifit_product_json(uuid)','neifit_order_json(uuid)','neifit_quote_json(uuid)',
  'neifit_create_document(uuid,text,uuid,jsonb)','neifit_read_orders(uuid,uuid,text)','neifit_read_quotes(uuid)',
  'neifit_update_order(uuid,uuid,text,text)','neifit_assign_delivery(uuid,uuid,uuid)',
  'neifit_update_quote(uuid,uuid,text)','neifit_save_product(uuid,jsonb,uuid)'
 ] loop
   execute 'revoke all on function public.'||signature||' from public,anon,authenticated';
   execute 'grant execute on function public.'||signature||' to service_role';
 end loop;
end;
$$;
notify pgrst,'reload schema';


-- ==================== migrations/0006_perfil_direcciones.sql ====================
-- Ejecutar después de 0005. No modifica pedidos ni datos existentes.
create table if not exists public.customer_addresses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  label text not null check(length(trim(label)) between 2 and 50),
  address text not null check(length(trim(address)) between 5 and 300),
  city text not null check(length(trim(city)) between 3 and 100),
  recipient text not null check(length(trim(recipient)) between 3 and 100),
  phone text not null check(length(trim(phone)) between 7 and 30),
  notes text not null default '' check(length(notes)<=500),
  created_at timestamptz not null default now()
);
create index if not exists customer_addresses_owner on public.customer_addresses(user_id);
alter table public.customer_addresses enable row level security;
revoke all on public.customer_addresses from public, anon, authenticated;
grant select on public.customer_addresses to authenticated;
grant select,insert,update,delete on public.customer_addresses to service_role;
drop policy if exists addresses_read_self on public.customer_addresses;
create policy addresses_read_self on public.customer_addresses for select to authenticated
using(user_id=(select auth.uid()) and public.neifit_has_permission('profile.read'));
notify pgrst,'reload schema';


-- ==================== migrations/0007_cotizaciones_avisos_cobros.sql ====================
-- Después de 0006. Avisos internos y cobros manuales auditados; sin pasarela.
-- Excluir escenarios simulados del indicador de ingresos sin borrar su historial.
create or replace function public.neifit_order_json(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select to_jsonb(o) - 'request_fingerprint' || jsonb_build_object(
   'is_simulated',exists(select 1 from public.payment_transactions t where t.order_id=o.id and (t.provider='simulacion_consultas' or t.raw_response->>'simulated'='true')),
   'assigned_delivery_name',p.full_name,
   'items',coalesce((select jsonb_agg(to_jsonb(i) order by i.id) from public.order_items i where i.order_id=o.id),'[]'::jsonb),
   'tracking_history',coalesce((select jsonb_agg(jsonb_build_object('status',t.status,'message',t.message,'timestamp',t.created_at) order by t.created_at,t.id)
     from public.order_tracking t where t.order_id=o.id),'[]'::jsonb))
 from public.orders o left join public.profiles p on p.id=o.assigned_delivery_user_id where o.id=p_id;
$$;
revoke all on function public.neifit_order_json(uuid) from public,anon,authenticated;
grant execute on function public.neifit_order_json(uuid) to service_role;
alter table public.quotes add column if not exists offered_total numeric(12,2) check(offered_total>0);
alter table public.quotes add column if not exists offer_conditions text;
alter table public.quotes add column if not exists offer_valid_until timestamptz;
alter table public.quotes add column if not exists responded_at timestamptz;
alter table public.quotes add column if not exists responded_by uuid references public.profiles(id);
create table if not exists public.notifications (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references public.profiles(id) on delete cascade,
 title text not null, message text not null, link text not null,
 created_at timestamptz not null default now(), read_at timestamptz
);
create index if not exists notifications_owner_date on public.notifications(user_id,created_at desc);
alter table public.notifications enable row level security;
revoke all on public.notifications from public,anon,authenticated;
grant select on public.notifications to authenticated;
grant select,insert,update on public.notifications to service_role;
drop policy if exists notifications_read_self on public.notifications;
create policy notifications_read_self on public.notifications for select to authenticated using(user_id=(select auth.uid()));

create or replace function public.neifit_document_notice() returns trigger
language plpgsql security definer set search_path='' as $$
declare v_number text; v_link text; v_title text;
begin
 if tg_table_name='orders' then
   v_number:=new.order_number; v_link:='/mis-pedidos';
   if tg_op='INSERT' then v_title:='Pedido registrado';
   elsif new.order_status is distinct from old.order_status then v_title:='Estado del pedido: '||new.order_status;
   elsif new.payment_status is distinct from old.payment_status then v_title:='Estado del pago: '||new.payment_status;
   else return new; end if;
 else
   v_number:=new.quote_number; v_link:='/mis-cotizaciones';
   if tg_op='INSERT' then v_title:='Cotización registrada';
   elsif new.status is distinct from old.status or new.responded_at is distinct from old.responded_at then v_title:='Cotización: '||new.status;
   else return new; end if;
 end if;
 insert into public.notifications(user_id,title,message,link) values(new.user_id,v_title,v_number,v_link);
 insert into public.notifications(user_id,title,message,link)
 select p.id,v_title,v_number,case when tg_table_name='orders' then '/admin?modulo=pedidos' else '/admin?modulo=cotizaciones' end
 from public.profiles p where p.id<>new.user_id and public.neifit_actor_can(p.id,case when tg_table_name='orders' then 'orders.manage' else 'quotes.manage' end);
 return new;
end;
$$;
drop trigger if exists order_notice on public.orders;
create trigger order_notice after insert or update on public.orders for each row execute function public.neifit_document_notice();
drop trigger if exists quote_notice on public.quotes;
create trigger quote_notice after insert or update on public.quotes for each row execute function public.neifit_document_notice();

create or replace function public.neifit_respond_quote(p_actor uuid,p_id uuid,p_total numeric,p_conditions text,p_valid_until timestamptz)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_status text;
begin
 if not public.neifit_actor_can(p_actor,'quotes.manage') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select status into v_status from public.quotes where id=p_id for update;
 if not found then raise exception 'Cotización no encontrada' using errcode='P0002'; end if;
 if v_status not in ('pendiente','respondida') then raise exception 'La cotización ya está cerrada' using errcode='P0001'; end if;
 if p_total is null or p_total<=0 or p_total>9999999999.99 or p_total::text in ('NaN','Infinity','-Infinity')
 or length(trim(coalesce(p_conditions,''))) not between 10 and 3000 or p_valid_until is null or p_valid_until<=now() then
   raise exception 'Indica precio total, condiciones y vigencia futura' using errcode='22023'; end if;
 update public.quotes set offered_total=p_total,offer_conditions=trim(p_conditions),offer_valid_until=p_valid_until,
 responded_at=clock_timestamp(),responded_by=p_actor,status='respondida' where id=p_id;
 insert into public.access_audit(actor_id,action,target,details) values(p_actor,'quote_response',p_id::text,jsonb_build_object('total',p_total,'valid_until',p_valid_until));
 return public.neifit_quote_json(p_id);
end;
$$;

create or replace function public.neifit_confirm_cash(p_actor uuid,p_id uuid,p_amount numeric,p_reference text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_order public.orders%rowtype;
begin
 if not exists(select 1 from public.profiles where id=p_actor and role='admin') then raise exception 'Administrador requerido' using errcode='42501'; end if;
 select * into v_order from public.orders where id=p_id for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if v_order.payment_method<>'contraentrega' or v_order.order_status<>'entregado' or v_order.payment_status not in ('pendiente','aprobado') then
 raise exception 'Solo se registra efectivo de pedidos contraentrega entregados' using errcode='P0001'; end if;
 if p_amount is distinct from v_order.total or length(trim(coalesce(p_reference,''))) not between 3 and 200 then
 raise exception 'El importe debe coincidir con el pedido e incluir referencia del recibo' using errcode='22023'; end if;
 if v_order.payment_status='aprobado' then
   if exists(select 1 from public.payment_transactions where order_id=p_id and provider='contraentrega_manual') then return public.neifit_order_json(p_id); end if;
   raise exception 'El pedido ya tiene otro pago aprobado' using errcode='P0001';
 end if;
 insert into public.payment_transactions(order_id,provider,provider_reference,amount,currency,status,raw_response)
 values(p_id,'contraentrega_manual',p_id::text,p_amount,'COP','aprobado',jsonb_build_object('recorded_by',p_actor,'receipt',trim(p_reference)));
 update public.orders set payment_status='aprobado' where id=p_id;
 insert into public.access_audit(actor_id,action,target,details) values(p_actor,'cash_received',p_id::text,jsonb_build_object('amount',p_amount,'receipt',trim(p_reference)));
 return public.neifit_order_json(p_id);
end;
$$;
revoke all on function public.neifit_document_notice(),public.neifit_respond_quote(uuid,uuid,numeric,text,timestamptz),public.neifit_confirm_cash(uuid,uuid,numeric,text) from public,anon,authenticated;
grant execute on function public.neifit_respond_quote(uuid,uuid,numeric,text,timestamptz),public.neifit_confirm_cash(uuid,uuid,numeric,text) to service_role;
notify pgrst,'reload schema';


commit;

-- Resultado final: 21 tablas y rowsecurity=true en todas.
select tablename, rowsecurity from pg_tables where schemaname='public'
and tablename = any(array['profiles','categories','products','carts','cart_items','orders','order_items','quotes','quote_items','order_tracking','payment_transactions','site_content','company_settings','company_values','permissions','role_permission_limits','role_permissions','access_audit','access_roles','customer_addresses','notifications'])
order by tablename;

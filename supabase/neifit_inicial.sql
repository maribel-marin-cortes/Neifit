-- NEIFIT: ejecutar completo en SQL Editor de un proyecto Supabase NUEVO.
-- No ejecutar sobre tablas existentes con otra estructura.
-- Sin productos/precios/stock ficticios. Las escrituras comerciales son del backend.
begin;

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

commit;
-- Comprobación: 14 tablas con RLS, 3 categorías, 5 contenidos, 6 valores.
select tablename, rowsecurity from pg_tables where schemaname = 'public'
and tablename in ('profiles','categories','products','carts','cart_items','orders','order_items',
 'quotes','quote_items','order_tracking','payment_transactions','site_content','company_settings','company_values')
order by tablename;

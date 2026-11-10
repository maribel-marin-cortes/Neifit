-- Ejecutar después del esquema inicial y 0002_catalogo_autenticado.sql.
-- No borra datos. Tras aplicarlo, activar RBAC_DATABASE_ENABLED=true en backend.
begin;
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
commit;

select role, count(*) as permisos from public.role_permissions group by role order by role;

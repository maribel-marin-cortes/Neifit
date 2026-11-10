-- Ejecutar después de 0003_roles_permisos.sql. No elimina usuarios ni datos.
begin;
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
commit;
select code,name from public.access_roles order by name;

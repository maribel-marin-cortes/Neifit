-- Aislamiento multiempresa reforzado, temas visuales y administración de plataforma.
-- Requiere 0011_multiempresa.sql y 0012_datos_demo_multiempresa.sql.
begin;

do $$ begin
 if to_regclass('public.empresas') is null or to_regclass('public.miembros_empresa') is null then
   raise exception 'Primero aplica las migraciones 0011 y 0012';
 end if;
end $$;

insert into public.permisos(codigo,descripcion) values
 ('appearance.manage','Gestionar apariencia de la empresa')
on conflict(codigo) do update set descripcion=excluded.descripcion;

insert into public.roles_acceso(codigo,nombre) values
 ('propietario','Propietario de empresa'),('vendedor','Vendedor')
on conflict(codigo) do update set nombre=excluded.nombre;

insert into public.limites_permisos_rol(rol,codigo_permiso)
select 'admin',codigo from public.permisos where codigo='appearance.manage'
on conflict do nothing;
insert into public.permisos_rol(rol,codigo_permiso)
select 'admin',codigo from public.permisos where codigo='appearance.manage'
on conflict do nothing;

insert into public.limites_permisos_rol(rol,codigo_permiso)
select 'propietario',codigo from public.permisos on conflict do nothing;
insert into public.permisos_rol(rol,codigo_permiso)
select 'propietario',codigo from public.permisos on conflict do nothing;
insert into public.limites_permisos_rol(rol,codigo_permiso)
select 'vendedor',codigo from public.permisos
where codigo in ('catalog.read','profile.read','products.manage','orders.manage','quotes.manage')
on conflict do nothing;
insert into public.permisos_rol(rol,codigo_permiso)
select 'vendedor',codigo from public.permisos
where codigo in ('catalog.read','profile.read','products.manage','orders.manage','quotes.manage')
on conflict do nothing;

create table public.roles_empresa (
 empresa_id uuid not null references public.empresas(id) on delete cascade,
 codigo text not null check(codigo ~ '^[a-z][a-z0-9_]{2,39}$'),
 nombre text not null check(length(btrim(nombre)) between 3 and 60),
 sistema boolean not null default false,
 creado_en timestamptz not null default now(),
 primary key(empresa_id,codigo)
);
create table public.permisos_rol_empresa (
 empresa_id uuid not null,
 rol text not null,
 codigo_permiso text not null references public.permisos(codigo),
 primary key(empresa_id,rol,codigo_permiso),
 foreign key(empresa_id,rol) references public.roles_empresa(empresa_id,codigo) on delete cascade
);
insert into public.roles_empresa(empresa_id,codigo,nombre,sistema)
select e.id,r.codigo,r.nombre,r.codigo in ('propietario','admin','cliente','mensajeria','vendedor')
from public.empresas e cross join public.roles_acceso r on conflict do nothing;
insert into public.permisos_rol_empresa(empresa_id,rol,codigo_permiso)
select e.id,rp.rol,rp.codigo_permiso from public.empresas e join public.permisos_rol rp on true
on conflict do nothing;
alter table public.miembros_empresa drop constraint if exists miembros_empresa_rol_fkey;
alter table public.miembros_empresa add constraint miembros_empresa_rol_empresa_fkey
 foreign key(empresa_id,rol) references public.roles_empresa(empresa_id,codigo);

create table public.temas_empresa (
 empresa_id uuid primary key references public.empresas(id) on delete cascade,
 color_primario text not null default '#7A4E2D' check(color_primario ~ '^#[0-9A-Fa-f]{6}$'),
 color_secundario text not null default '#5F8D4E' check(color_secundario ~ '^#[0-9A-Fa-f]{6}$'),
 color_acento text not null default '#D98CA4' check(color_acento ~ '^#[0-9A-Fa-f]{6}$'),
 color_fondo text not null default '#F6E7D8' check(color_fondo ~ '^#[0-9A-Fa-f]{6}$'),
 color_superficie text not null default '#FFF8F2' check(color_superficie ~ '^#[0-9A-Fa-f]{6}$'),
 color_texto text not null default '#4B2E1F' check(color_texto ~ '^#[0-9A-Fa-f]{6}$'),
 url_logo text check(url_logo is null or url_logo ~ '^(https://|/)[^[:space:]]+$'),
 url_icono text check(url_icono is null or url_icono ~ '^(https://|/)[^[:space:]]+$'),
 url_portada text check(url_portada is null or url_portada ~ '^(https://|/)[^[:space:]]+$'),
 tipografia_titulos text not null default 'Poppins' check(tipografia_titulos in ('Poppins','Montserrat','Inter','Lora','Roboto')),
 tipografia_texto text not null default 'Inter' check(tipografia_texto in ('Inter','Roboto','Montserrat','Lora','Poppins')),
 radio_bordes smallint not null default 16 check(radio_bordes between 0 and 32),
 estilo_botones text not null default 'solido' check(estilo_botones in ('solido','contorno','suave')),
 publicado boolean not null default true,
 actualizado_por uuid references public.perfiles(id),
 actualizado_en timestamptz not null default now()
);
insert into public.temas_empresa(empresa_id,url_logo)
select e.id,c.url_logo from public.empresas e
left join public.configuracion_empresa c on c.empresa_id=e.id
on conflict(empresa_id) do nothing;

create table public.superadministradores_plataforma (
 usuario_id uuid primary key references public.perfiles(id) on delete cascade,
 activo boolean not null default true,
 creado_en timestamptz not null default now(),
 creado_por uuid references public.perfiles(id)
);

alter table public.auditoria_acceso add column if not exists empresa_id uuid references public.empresas(id);
update public.auditoria_acceso a set empresa_id=coalesce(
 nullif(a.detalles->>'empresa_id','')::uuid,
 (select m.empresa_id from public.miembros_empresa m where m.usuario_id=a.actor_id order by m.creado_en limit 1),
 '00000000-0000-0000-0000-000000000001'::uuid)
where empresa_id is null;
alter table public.auditoria_acceso alter column empresa_id set not null;
alter table public.auditoria_acceso alter column empresa_id set default public.neifit_empresa_contexto();
create index if not exists auditoria_acceso_empresa_fecha on public.auditoria_acceso(empresa_id,creado_en desc);

alter table public.temas_empresa enable row level security;
alter table public.superadministradores_plataforma enable row level security;
alter table public.roles_empresa enable row level security;
alter table public.permisos_rol_empresa enable row level security;
revoke all on public.temas_empresa,public.superadministradores_plataforma from public,anon,authenticated;
revoke all on public.roles_empresa,public.permisos_rol_empresa from public,anon,authenticated;
grant select on public.temas_empresa to anon,authenticated,service_role;
grant select,insert,update,delete on public.roles_empresa,public.permisos_rol_empresa to service_role;
grant insert,update,delete on public.temas_empresa to service_role;
grant select,insert,update,delete on public.superadministradores_plataforma to service_role;
create policy temas_publicados on public.temas_empresa for select to anon,authenticated
 using(publicado and exists(select 1 from public.empresas e where e.id=empresa_id and e.estado='activa'));

create or replace function public.neifit_actor_puede(p_actor uuid,p_codigo text) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.miembros_empresa m
  where m.empresa_id=public.neifit_empresa_contexto() and m.usuario_id=p_actor and m.estado='activo'
  and (m.rol='propietario'
    or exists(select 1 from public.permisos_rol_empresa rp
      where rp.empresa_id=m.empresa_id and rp.rol=m.rol and rp.codigo_permiso=p_codigo)))
$$;

create or replace function public.neifit_aviso_documento() returns trigger
language plpgsql security definer set search_path='' as $$
declare v_numero text; v_enlace text; v_titulo text; v_permiso text;
begin
 if tg_table_name='pedidos' then
   v_numero:=new.numero_pedido; v_enlace:='/mis-pedidos'; v_permiso:='orders.manage';
   if tg_op='INSERT' then v_titulo:='Pedido registrado';
   elsif new.estado_pedido is distinct from old.estado_pedido then v_titulo:='Estado del pedido: '||new.estado_pedido;
   elsif new.estado_pago is distinct from old.estado_pago then v_titulo:='Estado del pago: '||new.estado_pago;
   else return new; end if;
 else
   v_numero:=new.numero_cotizacion; v_enlace:='/mis-cotizaciones'; v_permiso:='quotes.manage';
   if tg_op='INSERT' then v_titulo:='Cotización registrada';
   elsif new.estado is distinct from old.estado or new.respondida_en is distinct from old.respondida_en then v_titulo:='Cotización: '||new.estado;
   else return new; end if;
 end if;
 insert into public.notificaciones(empresa_id,usuario_id,titulo,mensaje,enlace)
 values(new.empresa_id,new.usuario_id,v_titulo,v_numero,v_enlace);
 insert into public.notificaciones(empresa_id,usuario_id,titulo,mensaje,enlace)
 select new.empresa_id,m.usuario_id,v_titulo,v_numero,
   case when tg_table_name='pedidos' then '/admin?modulo=pedidos' else '/admin?modulo=cotizaciones' end
 from public.miembros_empresa m where m.empresa_id=new.empresa_id and m.usuario_id<>new.usuario_id
   and m.estado='activo' and (m.rol='propietario' or exists(select 1 from public.permisos_rol_empresa rp
     where rp.empresa_id=m.empresa_id and rp.rol=m.rol and rp.codigo_permiso=v_permiso));
 return new;
end $$;

create or replace function public.neifit_confirmar_efectivo(p_actor uuid,p_id uuid,p_importe numeric,p_referencia text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare pedido public.pedidos%rowtype;
begin
 if not exists(select 1 from public.miembros_empresa where empresa_id=public.neifit_empresa_contexto()
   and usuario_id=p_actor and rol in ('propietario','admin') and estado='activo') then
   raise exception 'Administrador requerido' using errcode='42501'; end if;
 select * into pedido from public.pedidos where id=p_id and empresa_id=public.neifit_empresa_contexto() for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 if pedido.metodo_pago<>'contraentrega' or pedido.estado_pedido<>'entregado'
   or pedido.estado_pago not in ('pendiente','aprobado') then
   raise exception 'Solo se registra efectivo de pedidos contraentrega entregados' using errcode='P0001'; end if;
 if p_importe is distinct from pedido.total or length(trim(coalesce(p_referencia,''))) not between 3 and 200 then
   raise exception 'El importe debe coincidir con el pedido e incluir referencia del recibo' using errcode='22023'; end if;
 if pedido.estado_pago='aprobado' then
   if exists(select 1 from public.transacciones_pago where pedido_id=p_id and empresa_id=pedido.empresa_id
     and proveedor='contraentrega_manual') then return public.neifit_pedido_json(p_id); end if;
   raise exception 'El pedido ya tiene otro pago aprobado' using errcode='P0001'; end if;
 insert into public.transacciones_pago(pedido_id,proveedor,referencia_proveedor,importe,moneda,estado,respuesta_cruda)
 values(p_id,'contraentrega_manual',p_id::text,p_importe,'COP','aprobado',
   jsonb_build_object('recorded_by',p_actor,'receipt',trim(p_referencia)));
 update public.pedidos set estado_pago='aprobado' where id=p_id and empresa_id=pedido.empresa_id;
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(pedido.empresa_id,p_actor,'cash_received',p_id::text,jsonb_build_object(
   'importe',p_importe,'receipt',trim(p_referencia)));
 return public.neifit_pedido_json(p_id);
end $$;

create or replace function public.neifit_confirmar_efectivo(p_actor uuid,p_id uuid,p_importe numeric,p_referencia text,p_empresa uuid)
returns jsonb language plpgsql security definer set search_path='' as $$ begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.pedidos where id=p_id and empresa_id=p_empresa) then
   raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 return public.neifit_confirmar_efectivo(p_actor,p_id,p_importe,p_referencia);
end $$;

create function public.neifit_establecer_permisos_rol_empresa(
 p_actor uuid,p_empresa uuid,p_rol text,p_permisos text[]) returns void
language plpgsql security definer set search_path='' as $$
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not public.neifit_actor_puede(p_actor,'access.manage') or p_rol in ('propietario','admin')
   or not exists(select 1 from public.roles_empresa where empresa_id=p_empresa and codigo=p_rol) then
   raise exception 'Cambio de permisos no permitido' using errcode='42501'; end if;
 if p_permisos is null or not ('profile.read'=any(p_permisos)) or exists(
   select 1 from unnest(p_permisos) x where x is null or x in ('access.manage','users.manage','appearance.manage')
   or not exists(select 1 from public.permisos p where p.codigo=x)) then
   raise exception 'Permisos no delegables' using errcode='42501'; end if;
 delete from public.permisos_rol_empresa where empresa_id=p_empresa and rol=p_rol;
 insert into public.permisos_rol_empresa(empresa_id,rol,codigo_permiso)
 select p_empresa,p_rol,x from (select distinct unnest(p_permisos) x) s;
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(p_empresa,p_actor,'set_company_role_permissions',p_rol,jsonb_build_object('permisos',p_permisos));
end $$;

create function public.neifit_crear_rol_empresa(
 p_actor uuid,p_empresa uuid,p_codigo text,p_nombre text,p_permisos text[]) returns void
language plpgsql security definer set search_path='' as $$
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not public.neifit_actor_puede(p_actor,'access.manage') then
   raise exception 'Acceso denegado' using errcode='42501'; end if;
 if p_codigo is null or p_codigo !~ '^[a-z][a-z0-9_]{2,39}$'
   or p_codigo in ('propietario','admin','cliente','mensajeria','vendedor')
   or length(btrim(coalesce(p_nombre,''))) not between 3 and 60
   or p_permisos is null or not ('profile.read'=any(p_permisos))
   or exists(select 1 from unnest(p_permisos) x where x in ('access.manage','users.manage','appearance.manage')
     or not exists(select 1 from public.permisos p where p.codigo=x)) then
   raise exception 'Rol o permisos inválidos' using errcode='22023'; end if;
 insert into public.roles_empresa(empresa_id,codigo,nombre) values(p_empresa,p_codigo,btrim(p_nombre));
 insert into public.permisos_rol_empresa(empresa_id,rol,codigo_permiso)
 select p_empresa,p_codigo,x from (select distinct unnest(p_permisos) x) s;
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(p_empresa,p_actor,'create_company_role',p_codigo,jsonb_build_object('nombre',btrim(p_nombre)));
end $$;

create or replace function public.neifit_asignar_rol(p_actor_id uuid,p_usuario_id uuid,p_rol text,p_empresa uuid)
returns void language plpgsql security definer set search_path='' as $$
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if p_actor_id=p_usuario_id or not public.neifit_actor_puede(p_actor_id,'access.manage')
   or not exists(select 1 from public.roles_empresa where empresa_id=p_empresa and codigo=p_rol) then
   raise exception 'Cambio de rol no permitido' using errcode='42501'; end if;
 insert into public.miembros_empresa(empresa_id,usuario_id,rol,estado)
 values(p_empresa,p_usuario_id,p_rol,'activo')
 on conflict(empresa_id,usuario_id) do update set rol=excluded.rol,estado='activo';
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(p_empresa,p_actor_id,'assign_company_role',p_usuario_id::text,jsonb_build_object('rol',p_rol));
end $$;

create or replace function public.neifit_guardar_tema(p_actor uuid,p_empresa uuid,p_tema jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare resultado public.temas_empresa%rowtype;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not public.neifit_actor_puede(p_actor,'appearance.manage') then
   raise exception 'No tienes permiso para editar la apariencia' using errcode='42501';
 end if;
 insert into public.temas_empresa(empresa_id,color_primario,color_secundario,color_acento,color_fondo,
   color_superficie,color_texto,url_logo,url_icono,url_portada,tipografia_titulos,tipografia_texto,
   radio_bordes,estilo_botones,publicado,actualizado_por)
 values(p_empresa,coalesce(p_tema->>'color_primario','#7A4E2D'),coalesce(p_tema->>'color_secundario','#5F8D4E'),
   coalesce(p_tema->>'color_acento','#D98CA4'),coalesce(p_tema->>'color_fondo','#F6E7D8'),
   coalesce(p_tema->>'color_superficie','#FFF8F2'),coalesce(p_tema->>'color_texto','#4B2E1F'),
   nullif(p_tema->>'url_logo',''),nullif(p_tema->>'url_icono',''),nullif(p_tema->>'url_portada',''),
   coalesce(p_tema->>'tipografia_titulos','Poppins'),coalesce(p_tema->>'tipografia_texto','Inter'),
   coalesce((p_tema->>'radio_bordes')::smallint,16),coalesce(p_tema->>'estilo_botones','solido'),
   coalesce((p_tema->>'publicado')::boolean,true),p_actor)
 on conflict(empresa_id) do update set
   color_primario=excluded.color_primario,color_secundario=excluded.color_secundario,
   color_acento=excluded.color_acento,color_fondo=excluded.color_fondo,color_superficie=excluded.color_superficie,
   color_texto=excluded.color_texto,url_logo=excluded.url_logo,url_icono=excluded.url_icono,
   url_portada=excluded.url_portada,tipografia_titulos=excluded.tipografia_titulos,
   tipografia_texto=excluded.tipografia_texto,radio_bordes=excluded.radio_bordes,
   estilo_botones=excluded.estilo_botones,publicado=excluded.publicado,
   actualizado_por=p_actor,actualizado_en=clock_timestamp()
 returning * into resultado;
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(p_empresa,p_actor,'update_company_theme',p_empresa::text,jsonb_build_object('publicado',resultado.publicado));
 return to_jsonb(resultado);
end $$;

create function public.neifit_puede_gestionar_archivos(p_empresa uuid,p_usuario uuid default auth.uid())
returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.miembros_empresa m
  where m.empresa_id=p_empresa and m.usuario_id=p_usuario and m.estado='activo'
  and (m.rol in ('propietario','admin') or exists(
    select 1 from public.permisos_rol_empresa rp where rp.empresa_id=m.empresa_id and rp.rol=m.rol
    and rp.codigo_permiso in ('appearance.manage','products.manage'))))
$$;

create or replace function public.neifit_crear_empresa(p_actor uuid,p_nombre text,p_slug text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare nueva public.empresas%rowtype;
begin
 if not exists(select 1 from public.perfiles where id=p_actor) then
   raise exception 'Perfil no autorizado' using errcode='42501'; end if;
 if p_nombre is null or length(btrim(p_nombre)) not between 3 and 100
   or p_slug is null or lower(p_slug) !~ '^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$' then
   raise exception 'Nombre o identificador de empresa inválido' using errcode='22023'; end if;
 insert into public.empresas(nombre,slug) values(btrim(p_nombre),lower(p_slug)) returning * into nueva;
 insert into public.roles_empresa(empresa_id,codigo,nombre,sistema)
 select nueva.id,codigo,nombre,codigo in ('propietario','admin','cliente','mensajeria','vendedor')
 from public.roles_acceso;
 insert into public.permisos_rol_empresa(empresa_id,rol,codigo_permiso)
 select nueva.id,rol,codigo_permiso from public.permisos_rol;
 insert into public.miembros_empresa(empresa_id,usuario_id,rol) values(nueva.id,p_actor,'propietario');
 insert into public.configuracion_empresa(empresa_id,nombre_negocio) values(nueva.id,nueva.nombre);
 insert into public.temas_empresa(empresa_id) values(nueva.id);
 insert into public.contenido_sitio(empresa_id,clave,titulo,cuerpo,publicado) values
  (nueva.id,'hero_title','Portada',nueva.nombre,true),
  (nueva.id,'hero_description','Presentación','Conoce nuestros productos y servicios.',true),
  (nueva.id,'about_us','Quiénes somos','Información pendiente de completar por la empresa.',true),
  (nueva.id,'mission','Misión','Información pendiente de completar por la empresa.',true),
  (nueva.id,'vision','Visión','Información pendiente de completar por la empresa.',true);
 return jsonb_build_object('id',nueva.id,'nombre',nueva.nombre,'slug',nueva.slug,'estado',nueva.estado,'rol','propietario');
end $$;

-- Recursos de cada empresa: empresas/{empresa_id}/{logos|productos|categorias|evidencias}/archivo
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('recursos-empresas','recursos-empresas',true,5242880,array['image/jpeg','image/png','image/webp','image/svg+xml'])
on conflict(id) do update set public=true,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;
drop policy if exists recursos_empresa_insertar on storage.objects;
drop policy if exists recursos_empresa_actualizar on storage.objects;
drop policy if exists recursos_empresa_eliminar on storage.objects;
create policy recursos_empresa_insertar on storage.objects for insert to authenticated with check(
 bucket_id='recursos-empresas' and name ~ '^empresas/[0-9a-f-]{36}/(logos|portadas|productos|categorias|evidencias)/[^/]+$'
 and public.neifit_puede_gestionar_archivos((storage.foldername(name))[2]::uuid));
create policy recursos_empresa_actualizar on storage.objects for update to authenticated using(
 bucket_id='recursos-empresas' and name ~ '^empresas/[0-9a-f-]{36}/(logos|portadas|productos|categorias|evidencias)/[^/]+$'
 and public.neifit_puede_gestionar_archivos((storage.foldername(name))[2]::uuid)) with check(
 bucket_id='recursos-empresas' and public.neifit_puede_gestionar_archivos((storage.foldername(name))[2]::uuid));
create policy recursos_empresa_eliminar on storage.objects for delete to authenticated using(
 bucket_id='recursos-empresas' and name ~ '^empresas/[0-9a-f-]{36}/(logos|portadas|productos|categorias|evidencias)/[^/]+$'
 and public.neifit_puede_gestionar_archivos((storage.foldername(name))[2]::uuid));

revoke all on function public.neifit_guardar_tema(uuid,uuid,jsonb) from public,anon,authenticated;
revoke all on function public.neifit_puede_gestionar_archivos(uuid,uuid) from public,anon;
grant execute on function public.neifit_puede_gestionar_archivos(uuid,uuid) to authenticated,service_role;
revoke all on function public.neifit_establecer_permisos_rol_empresa(uuid,uuid,text,text[]),
 public.neifit_crear_rol_empresa(uuid,uuid,text,text,text[]) from public,anon,authenticated;
grant execute on function public.neifit_guardar_tema(uuid,uuid,jsonb),
 public.neifit_establecer_permisos_rol_empresa(uuid,uuid,text,text[]),
 public.neifit_crear_rol_empresa(uuid,uuid,text,text,text[]) to service_role;
notify pgrst,'reload schema';
commit;

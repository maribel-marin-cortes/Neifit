-- Completa el alta de mensajeros: identidad bloqueada, aprobación empresarial y auditoría.
-- Requiere 0014_solicitudes_mensajeria.sql.
begin;

do $$ begin
 if to_regclass('public.solicitudes_mensajeria') is null then
   raise exception 'Primero aplica 0014_solicitudes_mensajeria.sql';
 end if;
end $$;

alter table public.solicitudes_mensajeria
 add column if not exists usuario_id uuid references auth.users(id) on delete set null,
 add column if not exists notas text not null default '' check(length(notas)<=500);

-- Compatibilidad con solicitudes creadas por 0014, cuando el navegador también creó Auth.
update public.solicitudes_mensajeria s set usuario_id=p.id
from public.perfiles p
where s.usuario_id is null and lower(p.correo)=lower(s.correo);

alter table public.solicitudes_mensajeria drop constraint if exists solicitudes_mensajeria_nombre_valido;
alter table public.solicitudes_mensajeria add constraint solicitudes_mensajeria_nombre_valido
 check(length(btrim(nombre_completo)) between 3 and 100);
alter table public.solicitudes_mensajeria drop constraint if exists solicitudes_mensajeria_correo_valido;
alter table public.solicitudes_mensajeria add constraint solicitudes_mensajeria_correo_valido
 check(correo ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$');
alter table public.solicitudes_mensajeria drop constraint if exists solicitudes_mensajeria_vehiculo_valido;
alter table public.solicitudes_mensajeria add constraint solicitudes_mensajeria_vehiculo_valido
 check(tipo_vehiculo in ('moto','bicicleta','carro','a_pie'));

create unique index if not exists solicitudes_pendientes_correo_empresa
 on public.solicitudes_mensajeria(empresa_id,lower(correo)) where estado='pendiente';
create unique index if not exists solicitudes_pendientes_documento_empresa
 on public.solicitudes_mensajeria(empresa_id,documento_identidad) where estado='pendiente';

-- La creación pública pasa exclusivamente por FastAPI; service_role omite RLS.
revoke insert on public.solicitudes_mensajeria from anon,authenticated;
drop policy if exists solicitudes_creacion on public.solicitudes_mensajeria;

create or replace function public.neifit_aprobar_solicitud_mensajeria(
 p_actor uuid,p_empresa uuid,p_solicitud uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare solicitud public.solicitudes_mensajeria%rowtype;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_solicitud::text,0));
 if not public.neifit_actor_puede(p_actor,'users.manage') then
   raise exception 'No tienes permiso para aprobar mensajeros' using errcode='42501';
 end if;
 select * into solicitud from public.solicitudes_mensajeria
 where id=p_solicitud and empresa_id=p_empresa for update;
 if not found then raise exception 'Solicitud de mensajería no encontrada' using errcode='P0002'; end if;
 if solicitud.estado<>'pendiente' then raise exception 'La solicitud ya fue revisada' using errcode='P0001'; end if;
 if solicitud.usuario_id is null or not exists(select 1 from auth.users u
   where u.id=solicitud.usuario_id and lower(u.email)=lower(solicitud.correo)) then
   raise exception 'La identidad de Auth no coincide con la solicitud' using errcode='P0001';
 end if;
 insert into public.miembros_empresa(empresa_id,usuario_id,rol,estado)
 values(p_empresa,solicitud.usuario_id,'mensajeria','activo')
 on conflict(empresa_id,usuario_id) do update set rol='mensajeria',estado='activo';
 update public.solicitudes_mensajeria set estado='aprobado',motivo_rechazo='',
   revisado_por=p_actor,revisado_en=clock_timestamp() where id=p_solicitud;
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(p_empresa,p_actor,'approve_delivery_request',p_solicitud::text,
   jsonb_build_object('usuario_id',solicitud.usuario_id,'correo',solicitud.correo));
 insert into public.notificaciones(empresa_id,usuario_id,titulo,mensaje,enlace)
 values(p_empresa,solicitud.usuario_id,'Solicitud de mensajero aprobada',
   'Tu cuenta fue aprobada. Ya puedes ingresar al panel de mensajería.','/mensajeria');
 return (select jsonb_build_object('id',s.id,'full_name',s.nombre_completo,'email',s.correo,
   'phone',s.telefono,'document_id',s.documento_identidad,'vehicle_type',s.tipo_vehiculo,
   'vehicle_plate',s.placa_vehiculo,'city',s.ciudad,'notes',s.notas,'status',s.estado,
   'rejection_reason',s.motivo_rechazo,'reviewed_by',s.revisado_por,
   'reviewed_at',s.revisado_en,'created_at',s.creado_en)
   from public.solicitudes_mensajeria s where s.id=p_solicitud);
end $$;

create or replace function public.neifit_rechazar_solicitud_mensajeria(
 p_actor uuid,p_empresa uuid,p_solicitud uuid,p_motivo text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare solicitud public.solicitudes_mensajeria%rowtype;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_solicitud::text,0));
 if not public.neifit_actor_puede(p_actor,'users.manage') then
   raise exception 'No tienes permiso para rechazar mensajeros' using errcode='42501';
 end if;
 select * into solicitud from public.solicitudes_mensajeria
 where id=p_solicitud and empresa_id=p_empresa for update;
 if not found then raise exception 'Solicitud de mensajería no encontrada' using errcode='P0002'; end if;
 if solicitud.estado<>'pendiente' then raise exception 'La solicitud ya fue revisada' using errcode='P0001'; end if;
 if length(btrim(coalesce(p_motivo,''))) not between 3 and 500 then
   raise exception 'Indica un motivo de rechazo válido' using errcode='22023';
 end if;
 update public.solicitudes_mensajeria set estado='rechazado',motivo_rechazo=btrim(p_motivo),
   revisado_por=p_actor,revisado_en=clock_timestamp() where id=p_solicitud;
 insert into public.auditoria_acceso(empresa_id,actor_id,accion,objetivo,detalles)
 values(p_empresa,p_actor,'reject_delivery_request',p_solicitud::text,
   jsonb_build_object('usuario_id',solicitud.usuario_id,'motivo',btrim(p_motivo)));
 return (select jsonb_build_object('id',s.id,'full_name',s.nombre_completo,'email',s.correo,
   'phone',s.telefono,'document_id',s.documento_identidad,'vehicle_type',s.tipo_vehiculo,
   'vehicle_plate',s.placa_vehiculo,'city',s.ciudad,'notes',s.notas,'status',s.estado,
   'rejection_reason',s.motivo_rechazo,'reviewed_by',s.revisado_por,
   'reviewed_at',s.revisado_en,'created_at',s.creado_en)
   from public.solicitudes_mensajeria s where s.id=p_solicitud);
end $$;

revoke all on function public.neifit_aprobar_solicitud_mensajeria(uuid,uuid,uuid),
 public.neifit_rechazar_solicitud_mensajeria(uuid,uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.neifit_aprobar_solicitud_mensajeria(uuid,uuid,uuid),
 public.neifit_rechazar_solicitud_mensajeria(uuid,uuid,uuid,text) to service_role;
notify pgrst,'reload schema';
commit;

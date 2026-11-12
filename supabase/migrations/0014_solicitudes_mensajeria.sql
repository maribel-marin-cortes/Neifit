-- Migración 0014: Solicitudes de registro y aprobación de mensajeros
create table if not exists public.solicitudes_mensajeria (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null default '00000000-0000-0000-0000-000000000001' references public.empresas(id) on delete cascade,
  nombre_completo text not null,
  correo text not null,
  telefono text not null,
  documento_identidad text not null,
  tipo_vehiculo text not null,
  placa_vehiculo text default '',
  ciudad text default 'Medellín',
  estado text not null default 'pendiente' check(estado in ('pendiente','aprobado','rechazado')),
  motivo_rechazo text default '',
  revisado_por uuid references public.perfiles(id),
  revisado_en timestamptz,
  creado_en timestamptz not null default now()
);

create index if not exists solicitudes_mensajeria_empresa_estado on public.solicitudes_mensajeria(empresa_id, estado);
create index if not exists solicitudes_mensajeria_correo on public.solicitudes_mensajeria(correo);

alter table public.solicitudes_mensajeria enable row level security;
revoke all on public.solicitudes_mensajeria from public;
grant select, insert on public.solicitudes_mensajeria to anon, authenticated;
grant select, insert, update, delete on public.solicitudes_mensajeria to service_role;

drop policy if exists solicitudes_lectura on public.solicitudes_mensajeria;
create policy solicitudes_lectura on public.solicitudes_mensajeria for select to authenticated
using (
  correo = (select email from auth.users where id = (select auth.uid()))
  or exists (
    select 1 from public.miembros_empresa m
    where m.empresa_id = public.solicitudes_mensajeria.empresa_id
      and m.usuario_id = (select auth.uid())
      and m.rol in ('admin', 'propietario')
  )
);

drop policy if exists solicitudes_creacion on public.solicitudes_mensajeria;
create policy solicitudes_creacion on public.solicitudes_mensajeria for insert to anon, authenticated
with check (true);


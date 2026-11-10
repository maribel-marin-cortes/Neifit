-- NEIFIT: actualizar una base que ya tiene las migraciones 0001-0005.
-- No borra pedidos, productos ni usuarios. Ejecutar TODO en SQL Editor.
begin;
do $$ begin
 if to_regprocedure('public.neifit_actor_can(uuid,text)') is null then
   raise exception 'Primero ejecutar activar_servicios_supabase.sql: falta la migración 0005';
 end if;
end; $$;

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
select tablename,rowsecurity from pg_tables where schemaname='public' and tablename in ('customer_addresses','notifications');

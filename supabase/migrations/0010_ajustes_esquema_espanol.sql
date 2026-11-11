-- Ajustes posteriores al instalador físico en español. No borra registros.
begin;

do $$
begin
  if to_regclass('public.notificaciones') is null then
    raise exception 'Primero ejecuta neifit_esquema_completo_espanol.sql';
  end if;
  if exists(select 1 from information_schema.columns
            where table_schema='public' and table_name='notificaciones' and column_name='link')
     and not exists(select 1 from information_schema.columns
            where table_schema='public' and table_name='notificaciones' and column_name='enlace') then
    alter table public.notificaciones rename column link to enlace;
  end if;
end;
$$;

create or replace function public.neifit_aviso_documento() returns trigger
language plpgsql security definer set search_path='' as $$
declare v_numero text; v_enlace text; v_titulo text;
begin
 if tg_table_name='pedidos' then
   v_numero:=new.numero_pedido; v_enlace:='/mis-pedidos';
   if tg_op='INSERT' then v_titulo:='Pedido registrado';
   elsif new.estado_pedido is distinct from old.estado_pedido then v_titulo:='Estado del pedido: '||new.estado_pedido;
   elsif new.estado_pago is distinct from old.estado_pago then v_titulo:='Estado del pago: '||new.estado_pago;
   else return new; end if;
 else
   v_numero:=new.numero_cotizacion; v_enlace:='/mis-cotizaciones';
   if tg_op='INSERT' then v_titulo:='Cotización registrada';
   elsif new.estado is distinct from old.estado or new.respondida_en is distinct from old.respondida_en then v_titulo:='Cotización: '||new.estado;
   else return new; end if;
 end if;
 insert into public.notificaciones(usuario_id,titulo,mensaje,enlace)
 values(new.usuario_id,v_titulo,v_numero,v_enlace);
 insert into public.notificaciones(usuario_id,titulo,mensaje,enlace)
 select p.id,v_titulo,v_numero,
   case when tg_table_name='pedidos' then '/admin?modulo=pedidos' else '/admin?modulo=cotizaciones' end
 from public.perfiles p
 where p.id<>new.usuario_id
   and public.neifit_actor_puede(p.id,case when tg_table_name='pedidos' then 'orders.manage' else 'quotes.manage' end);
 return new;
end;
$$;

revoke all on function public.neifit_aviso_documento() from public,anon,authenticated;
notify pgrst,'reload schema';
commit;

select column_name from information_schema.columns
where table_schema='public' and table_name='notificaciones'
order by ordinal_position;

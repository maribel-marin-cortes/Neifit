-- Flujo logístico corto: recibido -> en_preparacion -> en_ruta -> entregado.
-- Conserva compatibilidad para pedidos que ya tengan estados del flujo anterior.
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
    v_permission:=case p_status when 'en_ruta' then 'delivery.start'
      when 'entregado' then 'delivery.complete' when 'novedad' then 'delivery.issue' else null end;
    if v_permission is null or not public.neifit_actor_can(p_actor,v_permission) then
      raise exception 'Acción de entrega no permitida' using errcode='42501'; end if;
    if p_status='novedad' and v_order.order_status not in ('en_preparacion','empacado','despachado','en_ruta') then
      raise exception 'La entrega todavía no permite registrar novedades' using errcode='P0001'; end if;
  end if;
  if v_order.order_status=p_status then return public.neifit_order_json(p_id); end if;
  if v_order.order_status in ('entregado','cancelado') or not (
    v_order.order_status='recibido' and p_status in ('en_preparacion','novedad','cancelado')
    or v_order.order_status='confirmado' and p_status in ('en_preparacion','novedad','cancelado')
    or v_order.order_status='en_preparacion' and p_status in ('en_ruta','novedad','cancelado')
    or v_order.order_status='empacado' and p_status in ('en_ruta','novedad','cancelado')
    or v_order.order_status='despachado' and p_status in ('en_ruta','novedad','cancelado')
    or v_order.order_status='en_ruta' and p_status in ('entregado','novedad')
    or v_order.order_status='novedad' and v_manage and p_status in ('en_preparacion','en_ruta','cancelado')
  ) then raise exception 'Transición de estado no permitida' using errcode='P0001'; end if;
  if p_status in ('en_ruta','entregado') and v_order.assigned_delivery_user_id is null then
    raise exception 'Asigna un mensajero antes de iniciar la ruta' using errcode='P0001'; end if;
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
revoke all on function public.neifit_update_order(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.neifit_update_order(uuid,uuid,text,text) to service_role;
notify pgrst,'reload schema';

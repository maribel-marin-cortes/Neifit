-- Corrige avisos multiempresa y permite registrar exclusivamente pagos simulados de demostración.
begin;

-- Las rutas corresponden a recursos públicos incluidos en frontend/public/images.
update public.categorias
set url_imagen=case identificador_url
  when 'postres' then '/images/postre-maracuya.png'
  when 'snacks' then '/images/cocadas.png'
  when 'bebidas' then '/images/bebidas-ilustrativas.png'
  else url_imagen end
where empresa_id=(select id from public.empresas where slug='neifit')
  and identificador_url in ('postres','snacks','bebidas');

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
 from public.miembros_empresa m
 where m.empresa_id=new.empresa_id and m.usuario_id<>new.usuario_id and m.estado='activo'
   and (m.rol='admin' or exists(select 1 from public.permisos_rol rp
     where rp.rol=m.rol and rp.codigo_permiso=v_permiso));
 return new;
end;
$$;

create or replace function public.neifit_registrar_pago_simulado(p_actor uuid,p_empresa uuid,p_id uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare pedido public.pedidos%rowtype;
begin
 perform pg_catalog.set_config('app.empresa_id',p_empresa::text,true);
 if not exists(select 1 from public.miembros_empresa where empresa_id=p_empresa
   and usuario_id=p_actor and rol='admin' and estado='activo') then
   raise exception 'Administrador requerido' using errcode='42501'; end if;
 select * into pedido from public.pedidos where id=p_id and empresa_id=p_empresa for update;
 if not found then raise exception 'Pedido no encontrado' using errcode='P0002'; end if;
 insert into public.transacciones_pago(empresa_id,pedido_id,proveedor,referencia_proveedor,
   importe,moneda,estado,respuesta_cruda)
 values(p_empresa,p_id,'simulacion_consultas','ESCENARIO-'||p_id::text,pedido.total,'COP','aprobado',
   jsonb_build_object('source','datos_inventados_autorizados','simulated',true,'real_funds',false))
 on conflict(proveedor,referencia_proveedor) do nothing;
 update public.pedidos set estado_pago='aprobado',metodo_pago='transferencia'
 where id=p_id and empresa_id=p_empresa;
 insert into public.auditoria_acceso(actor_id,accion,objetivo,detalles)
 values(p_actor,'simulated_payment',p_id::text,jsonb_build_object(
   'empresa_id',p_empresa,'simulated',true,'real_funds',false));
 return public.neifit_pedido_json(p_id);
end $$;

revoke all on function public.neifit_aviso_documento(),
 public.neifit_registrar_pago_simulado(uuid,uuid,uuid) from public,anon,authenticated;
grant execute on function public.neifit_registrar_pago_simulado(uuid,uuid,uuid) to service_role;
notify pgrst,'reload schema';
commit;

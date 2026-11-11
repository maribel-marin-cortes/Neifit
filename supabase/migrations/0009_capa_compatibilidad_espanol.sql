-- ETAPA 1 DE LA MIGRACION INTEGRAL A ESPANOL.
-- Agrega nombres espanoles sin renombrar ni borrar las tablas actuales.
-- Las vistas usan los permisos/RLS de las tablas originales (security_invoker).
-- Esto permite desplegar backend y frontend traducidos antes del renombre fisico final.
begin;

create or replace view public.perfiles with (security_invoker=true) as
select id,full_name as nombre_completo,email as correo,phone as telefono,role as rol,
       created_at as creado_en,updated_at as actualizado_en from public.profiles;
create or replace view public.categorias with (security_invoker=true) as
select id,name as nombre,slug as identificador_url,description as descripcion,image as imagen,
       is_active as activo from public.categories;
create or replace view public.productos with (security_invoker=true) as
select id,category_id as categoria_id,name as nombre,slug as identificador_url,description as descripcion,
       ingredients as ingredientes,allergens as alergenos,price as precio,stock as existencias,
       is_active as activo,is_available as disponible,image_url as url_imagen,featured as destacado,
       created_at as creado_en,updated_at as actualizado_en from public.products;
create or replace view public.carritos with (security_invoker=true) as
select id,user_id as usuario_id,status as estado,created_at as creado_en,updated_at as actualizado_en
from public.carts;
create or replace view public.elementos_carrito with (security_invoker=true) as
select id,cart_id as carrito_id,product_id as producto_id,quantity as cantidad,
       unit_price as precio_unitario,subtotal from public.cart_items;
create or replace view public.pedidos with (security_invoker=true) as
select id,user_id as usuario_id,order_number as numero_pedido,customer_name as nombre_cliente,
       customer_phone as telefono_cliente,customer_email as correo_cliente,address as direccion,
       order_status as estado_pedido,payment_status as estado_pago,payment_method as metodo_pago,
       subtotal,shipping_cost as costo_envio,total,notes as notas,
       assigned_delivery_user_id as usuario_mensajero_asignado_id,request_id as solicitud_id,
       request_fingerprint as huella_solicitud,stock_debited as existencias_descontadas,
       created_at as creado_en,updated_at as actualizado_en from public.orders;
create or replace view public.elementos_pedido with (security_invoker=true) as
select id,order_id as pedido_id,product_id as producto_id,product_name as nombre_producto,
       quantity as cantidad,unit_price as precio_unitario,subtotal from public.order_items;
create or replace view public.cotizaciones with (security_invoker=true) as
select id,user_id as usuario_id,quote_number as numero_cotizacion,status as estado,
       customer_name as nombre_cliente,customer_phone as telefono_cliente,customer_email as correo_cliente,
       notes as notas,request_id as solicitud_id,request_fingerprint as huella_solicitud,
       offered_total as total_ofrecido,offer_conditions as condiciones_oferta,
       offer_valid_until as oferta_valida_hasta,responded_at as respondida_en,
       responded_by as respondida_por,created_at as creado_en,updated_at as actualizado_en
from public.quotes;
create or replace view public.elementos_cotizacion with (security_invoker=true) as
select id,quote_id as cotizacion_id,product_id as producto_id,product_name as nombre_producto,
       quantity as cantidad,reference_price as precio_referencia from public.quote_items;
create or replace view public.seguimiento_pedidos with (security_invoker=true) as
select id,order_id as pedido_id,status as estado,message as mensaje,updated_by as actualizado_por,
       created_at as creado_en from public.order_tracking;
create or replace view public.transacciones_pago with (security_invoker=true) as
select id,order_id as pedido_id,provider as proveedor,provider_reference as referencia_proveedor,
       amount as importe,currency as moneda,status as estado,raw_response as respuesta_cruda,
       created_at as creado_en from public.payment_transactions;
create or replace view public.contenido_sitio with (security_invoker=true) as
select id,key as clave,title as titulo,body as cuerpo,is_published as publicado,
       updated_by as actualizado_por,updated_at as actualizado_en from public.site_content;
create or replace view public.configuracion_empresa with (security_invoker=true) as
select id,singleton as unico,business_name as nombre_negocio,phone_public as telefono_publico,
       whatsapp_number as numero_whatsapp,address as direccion,city as ciudad,
       opening_hours as horario_atencion,map_url as url_mapa,logo_url as url_logo,
       shipping_cost as costo_envio,updated_at as actualizado_en from public.company_settings;
create or replace view public.valores_empresa with (security_invoker=true) as
select id,title as titulo,description as descripcion,sort_order as orden,is_published as publicado
from public.company_values;
create or replace view public.permisos with (security_invoker=true) as
select code as codigo,description as descripcion from public.permissions;
create or replace view public.limites_permisos_rol with (security_invoker=true) as
select role as rol,permission_code as codigo_permiso from public.role_permission_limits;
create or replace view public.permisos_rol with (security_invoker=true) as
select role as rol,permission_code as codigo_permiso from public.role_permissions;
create or replace view public.auditoria_acceso with (security_invoker=true) as
select id,actor_id as actor_id,action as accion,target as objetivo,details as detalles,
       created_at as creado_en from public.access_audit;
create or replace view public.roles_acceso with (security_invoker=true) as
select code as codigo,name as nombre,created_at as creado_en from public.access_roles;
create or replace view public.direcciones_cliente with (security_invoker=true) as
select id,user_id as usuario_id,label as etiqueta,address as direccion,city as ciudad,
       recipient as destinatario,phone as telefono,notes as notas,created_at as creado_en
from public.customer_addresses;
create or replace view public.notificaciones with (security_invoker=true) as
select id,user_id as usuario_id,title as titulo,message as mensaje,link as enlace,
       created_at as creado_en,read_at as leido_en from public.notifications;

revoke all on public.perfiles,public.categorias,public.productos,public.carritos,public.elementos_carrito,
 public.pedidos,public.elementos_pedido,public.cotizaciones,public.elementos_cotizacion,
 public.seguimiento_pedidos,public.transacciones_pago,public.contenido_sitio,public.configuracion_empresa,
 public.valores_empresa,public.permisos,public.limites_permisos_rol,public.permisos_rol,
 public.auditoria_acceso,public.roles_acceso,public.direcciones_cliente,public.notificaciones
from public,anon,authenticated,service_role;
grant all on public.perfiles,public.categorias,public.productos,public.carritos,public.elementos_carrito,
 public.pedidos,public.elementos_pedido,public.cotizaciones,public.elementos_cotizacion,
 public.seguimiento_pedidos,public.transacciones_pago,public.contenido_sitio,public.configuracion_empresa,
 public.valores_empresa,public.permisos,public.limites_permisos_rol,public.permisos_rol,
 public.auditoria_acceso,public.roles_acceso,public.direcciones_cliente,public.notificaciones
to service_role;
grant select on public.categorias,public.contenido_sitio,public.configuracion_empresa,public.valores_empresa
to anon,authenticated;
grant select on public.productos,public.perfiles,public.carritos,public.elementos_carrito,public.pedidos,
 public.elementos_pedido,public.cotizaciones,public.elementos_cotizacion,public.seguimiento_pedidos,
 public.permisos,public.permisos_rol,public.direcciones_cliente,public.notificaciones to authenticated;
grant update(nombre_completo,telefono) on public.perfiles to authenticated;

create or replace function public.neifit_tiene_permiso(p_codigo text) returns boolean
language sql stable security definer set search_path='' as $$
 select public.neifit_has_permission(p_codigo);
$$;
create or replace function public.neifit_actor_puede(p_actor uuid,p_codigo text) returns boolean
language sql stable security definer set search_path='' as $$
 select public.neifit_actor_can(p_actor,p_codigo);
$$;
create or replace function public.neifit_asignar_rol(p_actor_id uuid,p_usuario_id uuid,p_rol text)
returns void language sql security definer set search_path='' as $$
 select public.neifit_assign_role(p_actor_id,p_usuario_id,p_rol);
$$;
create or replace function public.neifit_establecer_permisos_rol(p_actor_id uuid,p_rol text,p_permisos text[])
returns void language sql security definer set search_path='' as $$
 select public.neifit_set_role_permissions(p_actor_id,p_rol,p_permisos);
$$;
create or replace function public.neifit_crear_rol(p_actor_id uuid,p_codigo text,p_nombre text,p_permisos text[])
returns void language sql security definer set search_path='' as $$
 select public.neifit_create_role(p_actor_id,p_codigo,p_nombre,p_permisos);
$$;
create or replace function public.neifit_leer_pedidos(p_actor uuid,p_id uuid default null,p_seguimiento text default null)
returns jsonb language sql stable security definer set search_path='' as $$
 select public.neifit_read_orders(p_actor,p_id,p_seguimiento);
$$;
create or replace function public.neifit_actualizar_pedido(p_actor uuid,p_id uuid,p_estado text,p_mensaje text default '')
returns jsonb language sql security definer set search_path='' as $$
 select public.neifit_update_order(p_actor,p_id,p_estado,p_mensaje);
$$;
create or replace function public.neifit_asignar_mensajero(p_actor uuid,p_id uuid,p_mensajero uuid)
returns jsonb language sql security definer set search_path='' as $$
 select public.neifit_assign_delivery(p_actor,p_id,p_mensajero);
$$;
create or replace function public.neifit_leer_cotizaciones(p_actor uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select public.neifit_read_quotes(p_actor);
$$;
create or replace function public.neifit_actualizar_cotizacion(p_actor uuid,p_id uuid,p_estado text) returns jsonb
language sql security definer set search_path='' as $$
 select public.neifit_update_quote(p_actor,p_id,p_estado);
$$;
create or replace function public.neifit_responder_cotizacion(p_actor uuid,p_id uuid,p_total numeric,p_conditions text,p_valid_until timestamptz)
returns jsonb language sql security definer set search_path='' as $$
 select public.neifit_respond_quote(p_actor,p_id,p_total,p_conditions,p_valid_until);
$$;
create or replace function public.neifit_confirmar_efectivo(p_actor uuid,p_id uuid,p_amount numeric,p_reference text)
returns jsonb language sql security definer set search_path='' as $$
 select public.neifit_confirm_cash(p_actor,p_id,p_amount,p_reference);
$$;

do $$
declare firma text;
begin
 foreach firma in array array[
  'neifit_tiene_permiso(text)','neifit_actor_puede(uuid,text)',
  'neifit_asignar_rol(uuid,uuid,text)','neifit_establecer_permisos_rol(uuid,text,text[])',
  'neifit_crear_rol(uuid,text,text,text[])',
  'neifit_leer_pedidos(uuid,uuid,text)','neifit_actualizar_pedido(uuid,uuid,text,text)',
  'neifit_asignar_mensajero(uuid,uuid,uuid)','neifit_leer_cotizaciones(uuid)',
  'neifit_actualizar_cotizacion(uuid,uuid,text)',
  'neifit_responder_cotizacion(uuid,uuid,numeric,text,timestamptz)',
  'neifit_confirmar_efectivo(uuid,uuid,numeric,text)'
 ] loop
   execute 'revoke all on function public.'||firma||' from public,anon,authenticated';
   execute 'grant execute on function public.'||firma||' to service_role';
 end loop;
end;
$$;
grant execute on function public.neifit_tiene_permiso(text) to authenticated;
notify pgrst,'reload schema';
commit;

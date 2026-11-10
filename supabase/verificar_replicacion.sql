-- Solo lectura. Ejecutar como propietario tras instalar el esquema completo.
do $$
declare tabla text;
begin
  foreach tabla in array array['profiles','categories','products','carts','cart_items',
    'orders','order_items','quotes','quote_items','order_tracking','payment_transactions',
    'site_content','company_settings','company_values','permissions','role_permission_limits',
    'role_permissions','access_audit','access_roles','customer_addresses','notifications'] loop
    if not exists(select 1 from pg_tables where schemaname='public' and tablename=tabla and rowsecurity) then
      raise exception 'Tabla ausente o sin RLS: %', tabla;
    end if;
  end loop;
  if (select count(*) from public.permissions) <> 16 then
    raise exception 'Se esperaban 16 permisos iniciales';
  end if;
  if (select count(*) from public.role_permissions where role='admin') <> 16
    or (select count(*) from public.role_permissions where role='cliente') <> 6
    or (select count(*) from public.role_permissions where role='mensajeria') <> 5 then
    raise exception 'Revisar permisos iniciales de los roles';
  end if;
  if (select count(*) from public.categories) <> 3
    or (select count(*) from public.site_content) <> 5
    or (select count(*) from public.company_values) <> 6 then
    raise exception 'Revisar datos institucionales iniciales';
  end if;
end;
$$;

select code, name from public.access_roles order by name;
select
  exists(select 1 from information_schema.columns where table_schema='public' and table_name='orders' and column_name='request_id') as pedidos_con_idempotencia,
  exists(select 1 from information_schema.columns where table_schema='public' and table_name='orders' and column_name='stock_debited') as inventario_controlado,
  has_function_privilege('service_role','public.neifit_create_document(uuid,text,uuid,jsonb)','EXECUTE') as servidor_crea_documentos,
  not has_function_privilege('authenticated','public.neifit_create_document(uuid,text,uuid,jsonb)','EXECUTE') as documentos_solo_servidor;
select
  not has_table_privilege('anon','public.products','SELECT') as catalogo_privado,
  not has_column_privilege('authenticated','public.profiles','role','UPDATE') as rol_protegido,
  not has_table_privilege('authenticated','public.orders','INSERT') as pedidos_solo_backend,
  not has_table_privilege('authenticated','public.access_roles','INSERT') as roles_sin_escritura_cliente,
  not has_function_privilege('authenticated','public.neifit_create_role(uuid,text,text,text[])','EXECUTE') as funcion_roles_privada,
  has_function_privilege('service_role','public.neifit_create_role(uuid,text,text,text[])','EXECUTE') as servidor_autorizado;

select id, public from storage.buckets where id in ('products','evidence') order by id;
-- products público; evidence privado. La consulta final debe mostrar todos true.
select
  exists(select 1 from storage.buckets where id='products' and public) as bucket_productos_correcto,
  exists(select 1 from storage.buckets where id='evidence' and not public) as bucket_evidencias_correcto;

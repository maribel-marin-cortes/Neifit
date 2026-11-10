-- Ejecutar DESPUÉS de neifit_inicial.sql. Solo lectura y transacciones revertidas.
select tablename, rowsecurity from pg_tables where schemaname = 'public'
and tablename in ('profiles','categories','products','carts','cart_items','orders','order_items',
 'quotes','quote_items','order_tracking','payment_transactions','site_content','company_settings','company_values')
order by tablename; -- Las 14 filas deben mostrar true.

select 'categories' as tabla, count(*) as registros from public.categories
union all select 'site_content', count(*) from public.site_content
union all select 'company_values', count(*) from public.company_values;
-- Inicialmente: 3, 5 y 6. products queda vacía hasta cargar productos reales.

begin;
set local role anon;
select count(*) as categorias_publicas from public.categories; -- 3
select count(*) as contenidos_publicos from public.site_content; -- 5
do $$
begin
  begin
    perform 1 from public.profiles;
    raise exception 'FALLO: anon puede leer profiles';
  exception when insufficient_privilege then
    raise notice 'OK: anon no tiene acceso a profiles';
  end;
end;
$$;
rollback;

begin;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-000000000001","role":"authenticated"}', true);
select count(*) as perfiles_ajenos_visibles from public.profiles; -- 0 para este UUID inexistente
do $$
begin
  if has_column_privilege(current_user, 'public.profiles', 'role', 'UPDATE') then
    raise exception 'FALLO: authenticated puede editar role';
  end if;
  if has_table_privilege(current_user, 'public.orders', 'INSERT') then
    raise exception 'FALLO: authenticated puede insertar pedidos directamente';
  end if;
  raise notice 'OK: rol protegido y pedidos reservados al backend';
end;
$$;
rollback;

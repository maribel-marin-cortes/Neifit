-- Ejecutar después de 0003_roles_permisos.sql. Solo consulta privilegios.
select role, count(*) as permisos from public.role_permissions group by role order by role;
select tablename, rowsecurity from pg_tables where schemaname='public'
and tablename in ('permissions','role_permissions','role_permission_limits','access_audit');

do $$
begin
  if has_table_privilege('authenticated','public.role_permissions','UPDATE')
    or has_table_privilege('authenticated','public.role_permissions','INSERT')
    or has_table_privilege('authenticated','public.role_permissions','DELETE') then
    raise exception 'FALLO: permisos editables directamente por authenticated';
  end if;
  if has_function_privilege('authenticated','public.neifit_assign_role(uuid,uuid,text)','EXECUTE')
    or has_function_privilege('anon','public.neifit_assign_role(uuid,uuid,text)','EXECUTE')
    or has_function_privilege('authenticated','public.neifit_set_role_permissions(uuid,text,text[])','EXECUTE')
    or has_function_privilege('anon','public.neifit_set_role_permissions(uuid,text,text[])','EXECUTE') then
    raise exception 'FALLO: funciones de gestión accesibles sin backend';
  end if;
  if has_table_privilege('authenticated','public.access_audit','SELECT')
    or has_table_privilege('anon','public.access_audit','SELECT') then
    raise exception 'FALLO: auditoría expuesta';
  end if;
  raise notice 'OK: tablas de permisos, funciones administrativas y auditoría protegidas';
end;
$$;

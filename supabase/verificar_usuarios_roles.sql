-- Solo lectura. Ejecutar tras instalar 0004.
select code, name from public.access_roles order by name;
select count(*) = 16 as catalogo_completo from public.permissions;
select count(*) = 16 as administrador_completo from public.role_permissions where role = 'admin';
select rowsecurity as roles_con_rls from pg_tables where schemaname = 'public' and tablename = 'access_roles';
select not has_table_privilege('authenticated','public.access_roles','INSERT') as roles_sin_escritura_cliente;
select not has_column_privilege('authenticated','public.profiles','role','UPDATE') as rol_protegido;
select not has_function_privilege('authenticated','public.neifit_create_role(uuid,text,text,text[])','EXECUTE') as crear_rol_solo_servidor;
select not has_function_privilege('anon','public.neifit_assign_role(uuid,uuid,text)','EXECUTE') as asignacion_privada;
select has_function_privilege('service_role','public.neifit_create_role(uuid,text,text,text[])','EXECUTE') as servidor_puede_crear_roles;
select not exists(select 1 from public.role_permission_limits where role <> 'admin' and permission_code in ('users.manage','access.manage')) as gestion_reservada_admin;

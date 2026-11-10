"""Construye la actualización sobre una base Neifit existente, sin borrar datos."""
from pathlib import Path

BASE=Path(__file__).resolve().parent
parts=['''-- ACTIVAR SERVICIOS EN UNA BASE NEIFIT YA INSTALADA.
-- Conserva datos y permisos. Ejecutar completo en SQL Editor.
-- Instala 0003/0004 solo si faltan sus tablas y aplica 0005.
begin;
do $$ begin
  if to_regclass('public.products') is null or to_regclass('public.orders') is null then
    raise exception 'Primero instala el esquema inicial de Neifit';
  end if;
end; $$;
revoke select on public.products from anon;
alter policy products_public on public.products to authenticated;
''']
for filename,table,tag in [('0003_roles_permisos.sql','permissions','rbac'),('0004_usuarios_roles_personalizados.sql','access_roles','roles')]:
    text=(BASE/'migrations'/filename).read_text(encoding='utf-8')
    text='\n'.join(line for line in text.splitlines() if line.strip().lower() not in ('begin;','commit;'))
    parts.append("do $install_"+tag+"$ begin if to_regclass('public."+table+"') is null then execute $migration_"+tag+"$\n"+text+"\n$migration_"+tag+"$; end if; end; $install_"+tag+"$;\n")
text=(BASE/'migrations/0005_servicios_comerciales.sql').read_text(encoding='utf-8')
parts.append('\n'.join(line for line in text.splitlines() if line.strip().lower() not in ('begin;','commit;')))
for filename in ['0006_perfil_direcciones.sql', '0007_cotizaciones_avisos_cobros.sql']:
    text=(BASE/'migrations'/filename).read_text(encoding='utf-8')
    parts.append('\n'.join(line for line in text.splitlines() if line.strip().lower() not in ('begin;', 'commit;')))
parts.append('\ncommit;\nselect code,name from public.access_roles order by name;\n')
(BASE/'activar_servicios_supabase.sql').write_text('\n'.join(parts),encoding='utf-8')
print('Actualización completa de servicios generada.')

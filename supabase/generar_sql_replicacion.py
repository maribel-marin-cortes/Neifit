"""Construye un instalador para un proyecto Supabase nuevo, sin leer credenciales."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

BASE = Path(__file__).resolve().parent
SOURCES = ['neifit_inicial.sql', 'migrations/0002_catalogo_autenticado.sql',
           'migrations/0003_roles_permisos.sql', 'migrations/0004_usuarios_roles_personalizados.sql',
           'migrations/0005_servicios_comerciales.sql', 'migrations/0006_perfil_direcciones.sql',
           'migrations/0007_cotizaciones_avisos_cobros.sql']
TABLES = ['profiles','categories','products','carts','cart_items','orders','order_items',
          'quotes','quote_items','order_tracking','payment_transactions','site_content',
          'company_settings','company_values','permissions','role_permission_limits',
          'role_permissions','access_audit','access_roles','customer_addresses','notifications']

header = '''-- NEIFIT: INSTALADOR COMPLETO PARA UN PROYECTO SUPABASE NUEVO.
-- Incluye esquema inicial y migraciones 0002, 0003, 0004, 0005, 0006 y 0007.
-- Ejecutar TODO una sola vez en Supabase > SQL Editor.
-- No ejecutar además los archivos originales: ya están incluidos aquí.
-- No contiene claves, contraseñas ni copias de usuarios/pedidos del proyecto original.
-- Conserva las categorías y los contenidos institucionales iniciales de Neifit.
-- No es un instalador de PostgreSQL genérico: requiere Supabase Auth y Storage.

begin;
do $$
begin
  if to_regclass('auth.users') is null or to_regclass('storage.buckets') is null then
    raise exception 'Requiere un proyecto Supabase con Auth y Storage disponibles';
  end if;
  if exists(select 1 from pg_tables where schemaname = 'public'
    and tablename = any(array[TABLE_NAMES])) then
    raise exception 'Ya existen tablas de Neifit. Utiliza un proyecto nuevo o revisa las migraciones pendientes. No se ha borrado ningún dato.';
  end if;
end;
$$;
'''.replace('TABLE_NAMES', ','.join("'" + name + "'" for name in TABLES))

parts = [header]
for source in SOURCES:
    content = (BASE/source).read_text(encoding='utf-8-sig')
    # Los BEGIN de funciones PL/pgSQL no llevan punto y coma y se conservan.
    content = '\n'.join(line for line in content.splitlines()
                        if line.strip().lower() not in ('begin;', 'commit;'))
    parts.append(f'\n-- ==================== {source} ====================\n{content}\n')
parts.append("\ncommit;\n\n-- Resultado final: 21 tablas y rowsecurity=true en todas.\n"
             "select tablename, rowsecurity from pg_tables where schemaname='public'\n"
             "and tablename = any(array[" + ','.join("'"+name+"'" for name in TABLES) + "])\norder by tablename;\n")
(BASE/'neifit_completo_base_nueva.sql').write_text('\n'.join(parts), encoding='utf-8')

with ZipFile(BASE/'Neifit_base_datos_para_compartir.zip', 'w', ZIP_DEFLATED) as package:
    for name in ['neifit_completo_base_nueva.sql', 'REPLICAR_BASE_DATOS.md', 'verificar_replicacion.sql']:
        package.write(BASE/name, name)
print('Instalador y ZIP listos: esquema completo, guía y verificación; sin credenciales.')

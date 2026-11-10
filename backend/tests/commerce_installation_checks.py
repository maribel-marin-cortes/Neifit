"""Comprueba instalador nuevo y actualización incremental en bases locales aisladas."""
import ast
import json
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg import sql

ROOT=Path(__file__).resolve().parents[2]
config=json.loads((ROOT/'tmp/commerce-test-db.json').read_text(encoding='utf-8-sig'))
if not Path(config['folder']).resolve().is_relative_to((ROOT/'tmp').resolve()):
    raise RuntimeError('Se requiere una instancia temporal local dentro de tmp')
connection=dict(host='127.0.0.1',port=config['port'],user='postgres',dbname='postgres')
tree=ast.parse((ROOT/'backend/tests/commerce_postgres_checks.py').read_text(encoding='utf-8'))
bootstrap=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bootstrap' for t in n.targets))
bootstrap='\n'.join(line for line in bootstrap.splitlines() if not line.startswith('create role '))

with psycopg.connect(**connection,autocommit=True) as owner:
    for mode in ['complete','upgrade']:
        name='neifit_test_'+mode+'_'+uuid4().hex[:10]
        owner.execute(sql.SQL('create database {}').format(sql.Identifier(name)))
        with psycopg.connect(**{**connection,'dbname':name},autocommit=True) as c:
            c.execute(bootstrap)
            if mode=='complete':
                c.execute((ROOT/'supabase/neifit_completo_base_nueva.sql').read_text(encoding='utf-8'))
            else:
                c.execute((ROOT/'supabase/neifit_inicial.sql').read_text(encoding='utf-8'))
                c.execute((ROOT/'supabase/activar_servicios_supabase.sql').read_text(encoding='utf-8'))
            c.execute((ROOT/'supabase/verificar_replicacion.sql').read_text(encoding='utf-8'))
            c.execute((ROOT/'supabase/preparar_piloto_produccion.sql').read_text(encoding='utf-8'))
            assert c.execute("select count(*) from pg_tables where schemaname='public' and rowsecurity").fetchone()[0]==21
            c.execute("delete from public.role_permissions where role='cliente' and permission_code='catalog.read'")
            c.execute((ROOT/'supabase/activar_servicios_supabase.sql').read_text(encoding='utf-8'))
            assert c.execute("select count(*) from public.role_permissions where role='cliente' and permission_code='catalog.read'").fetchone()[0]==0
            assert c.execute("select count(*) from public.categories").fetchone()[0]==3
            assert c.execute("select public.neifit_read_orders('00000000-0000-0000-0000-000000000000',null,null)").fetchone()[0]==[]
            print('OK instalación '+mode+': 21 tablas, verificación completa y actualización repetida conserva permisos.')

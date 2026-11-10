"""Ensayo de respaldo/restauración completo en la instancia temporal local."""
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
config = json.loads((ROOT/'tmp/commerce-test-db.json').read_text(encoding='utf-8'))
assert Path(config['folder']).resolve().is_relative_to((ROOT/'tmp').resolve())
bins = sorted(Path('C:/Program Files/PostgreSQL').glob('*/bin/pg_dump.exe'), reverse=True)[0].parent
connection = dict(host='127.0.0.1', port=config['port'], user='postgres', dbname='postgres')
target = 'neifit_restore_' + uuid4().hex[:12]
dump = Path(config['folder'])/'restore-check.dump'
with psycopg.connect(**connection, autocommit=True) as c:
    expected = c.execute("select (select count(*) from public.orders),(select count(*) from public.profiles),(select count(*) from public.notifications),(select count(*) from public.payment_transactions)").fetchone()
    c.execute(sql.SQL('create database {}').format(sql.Identifier(target)))
env = {**os.environ, 'PGHOST': '127.0.0.1', 'PGPORT': str(config['port']), 'PGUSER': 'postgres', 'PGDATABASE': 'postgres'}
subprocess.run([str(bins/'pg_dump.exe'), '--format=custom', '--file', str(dump)], env=env, check=True, capture_output=True)
subprocess.run([str(bins/'pg_restore.exe'), '--exit-on-error', '--dbname', target, str(dump)], env=env, check=True, capture_output=True)
with psycopg.connect(**{**connection, 'dbname': target}) as c:
    actual = c.execute("select (select count(*) from public.orders),(select count(*) from public.profiles),(select count(*) from public.notifications),(select count(*) from public.payment_transactions)").fetchone()
    assert actual == expected
    assert c.execute("select count(*) from pg_tables where schemaname='public' and rowsecurity").fetchone()[0] == 21
    assert not c.execute("select has_function_privilege('authenticated','public.neifit_confirm_cash(uuid,uuid,numeric,text)','EXECUTE')").fetchone()[0]
print('OK respaldo/restauración local: pedidos, perfiles, avisos, cobros, 21 tablas RLS y privilegios conservados.')

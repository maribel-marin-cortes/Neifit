"""Crea una instancia LOCAL temporal y comprueba instalación/negocio/navegador.

Desde la raíz:
uv run --no-project --with 'psycopg[binary]' --with playwright --python backend/.venv/Scripts/python.exe python backend/tests/run_commerce_checks.py --browser
No lee .env, no se conecta al Supabase remoto ni elimina archivos existentes.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--browser',action='store_true',help='Requiere Vite iniciado en el puerto 5173')
args=parser.parse_args()
bins=sorted(Path('C:/Program Files/PostgreSQL').glob('*/bin/initdb.exe'),reverse=True)
if not bins:raise SystemExit('No se encontró PostgreSQL local. Estas pruebas no utilizan bases remotas.')
bin=bins[0].parent
tmp=ROOT/'tmp';tmp.mkdir(exist_ok=True)
folder=Path(tempfile.mkdtemp(prefix='neifit_postgres_',dir=tmp)).resolve()
assert folder.is_relative_to(tmp.resolve())
with socket.socket() as listener:
    listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
hidden=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0

def run_pg(command):
    # No usar PIPE al iniciar postgres: el servidor heredaría sus handles.
    with (folder/'control.log').open('ab') as output:
        subprocess.run(command,stdout=output,stderr=output,check=True,creationflags=hidden,timeout=90)

started=False
try:
    run_pg([str(bin/'initdb.exe'),'-D',str(folder/'data'),'-U','postgres','-A','trust','--encoding=UTF8','--locale=C'])
    run_pg([str(bin/'pg_ctl.exe'),'-D',str(folder/'data'),'-l',str(folder/'postgres.log'),'-o',f'-h 127.0.0.1 -p {port}','-w','start'])
    started=True
    (tmp/'commerce-test-db.json').write_text(json.dumps({'folder':str(folder),'port':port}),encoding='utf-8')
    for test in ['commerce_postgres_checks.py','commerce_installation_checks.py','commerce_backup_checks.py']+(['commerce_browser_checks.py'] if args.browser else []):
        subprocess.run([sys.executable,str(ROOT/'backend/tests'/test)],check=True,cwd=ROOT)
finally:
    if started:
        run_pg([str(bin/'pg_ctl.exe'),'-D',str(folder/'data'),'-m','fast','-w','stop'])
        (tmp/'commerce-test-db.json').write_text(json.dumps({'folder':str(folder),'port':port,'stopped':True}),encoding='utf-8')
print('Pruebas completas; PostgreSQL temporal detenido. Logs conservados en tmp.')

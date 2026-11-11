"""Carga idempotente de demostración para el esquema español multiempresa.

No se ejecuta sin ``--aplicar``. Los pagos aprobados son simulaciones contables
identificadas; no llama a pasarelas ni envía correos. Las contraseñas nunca se
guardan en el repositorio y solo se leen de variables de entorno.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT / 'backend/.env', override=True)
os.environ['DEBUG'] = 'true'

import httpx
from app.core.config import settings
from app.core.supabase_headers import service_headers
from app.core.supabase_rest import supabase_rest as db

PRODUCTOS = [
 ('Postre de Maracuyá','postre-maracuya','postres',12500,12,'postre-maracuya','Postre de maracuyá de la selección Neifit.'),
 ('Mousse de Mango','mousse-mango','postres',13000,10,'mousse-mango','Mousse de mango de nuestra selección de postres.'),
 ('Postre de Fresa','postre-fresa','postres',13500,8,'postre-fresa','Postre de fresa para acompañar tus momentos especiales.'),
 ('Postre de Melocotón','postre-melocoton','postres',12800,6,'postre-melocoton','Postre de melocotón de la selección Neifit.'),
 ('Postre de Chontaduro','postre-chontaduro','postres',14500,3,'torta-chontaduro','Postre de chontaduro de nuestra selección de sabores tropicales.'),
 ('Postre Regional','postre-regional','postres',14000,0,'postre-regional','Una opción de nuestra selección de postres regionales.'),
 ('Cocadas','cocadas','snacks',8500,15,'cocadas','Cocadas de la selección de snacks Neifit.'),
 ('Dátiles con Crema de Maní','datiles-mani','snacks',11000,12,'datiles-mani','Dátiles con crema de maní de nuestra selección de snacks.'),
 ('Maní Tostado','mani-tostado','snacks',6000,3,'mani-tostado','Maní tostado para disfrutar como snack.'),
 ('Mix de Frutos Secos','mix-frutos-secos','snacks',12000,10,'mix-frutos-secos','Mix de frutos secos para acompañar tus momentos del día.'),
 ('Bebida Tropical 1','bebida-tropical-1','bebidas',22000,8,'bebidas-ilustrativas','Bebida de la selección tropical Neifit.'),
 ('Bebida Tropical 2','bebida-tropical-2','bebidas',24000,6,'bebidas-ilustrativas','Otra opción de nuestra selección de bebidas tropicales.'),
 ('Bebida Tropical 3','bebida-tropical-3','bebidas',25000,5,'bebidas-ilustrativas','Bebida para acompañar tus postres y snacks favoritos.'),
]
USUARIOS = [
 ('admin@neifit.com','Administrador General','admin','NEIFIT_DEMO_ADMIN_PASSWORD'),
 ('mensajeria@neifit.com','Carlos Mensajero Neifit','mensajeria','NEIFIT_DEMO_MENSAJERIA_PASSWORD'),
 ('cliente@neifit.com','María Fernanda Gómez','cliente','NEIFIT_DEMO_CLIENTE_PASSWORD'),
]
CLIENTES = [
 {'nombre_cliente':'Camila Torres','telefono_cliente':'+57 300 000 0101','correo_cliente':'camila.torres@example.com','direccion':'Carrera 45 # 12-30, Medellín'},
 {'nombre_cliente':'Mateo Ríos','telefono_cliente':'+57 300 000 0102','correo_cliente':'mateo.rios@example.com','direccion':'Calle 32 # 65-18, Medellín'},
 {'nombre_cliente':'Laura Gómez','telefono_cliente':'+57 300 000 0103','correo_cliente':'laura.gomez@example.com','direccion':'Carrera 70 # 44-25, Medellín'},
]


async def asegurar_usuario(client, empresa_id, email, nombre, rol, variable_password, crear):
    perfiles = await db.rows('perfiles', {'correo':'eq.' + email, 'select':'id,correo,rol'})
    if not perfiles:
        if not crear:
            raise RuntimeError(f'No existe {email}. Usa --crear-usuarios-demo o indica --administrador.')
        password = os.getenv(variable_password, '')
        if not 8 <= len(password) <= 128:
            raise RuntimeError(f'Falta {variable_password} con una contraseña de 8 a 128 caracteres')
        response = await client.post(settings.SUPABASE_URL.rstrip('/') + '/auth/v1/admin/users',
            headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY), json={
              'email':email, 'password':password, 'email_confirm':True,
              'user_metadata':{'nombre_completo':nombre,'full_name':nombre,'telefono':'3000000000'}})
        response.raise_for_status()
        user_id = response.json()['id']
        perfiles = await db.rows('perfiles', {'id':'eq.' + user_id, 'select':'id,correo,rol'})
    if len(perfiles) != 1:
        raise RuntimeError('Identidad ambigua para ' + email)
    user_id = perfiles[0]['id']
    await db.request('POST','miembros_empresa',params={'on_conflict':'empresa_id,usuario_id'},
        data={'empresa_id':empresa_id,'usuario_id':user_id,'rol':rol,'estado':'activo'},
        headers={'Prefer':'resolution=merge-duplicates'})
    if rol == 'admin' and perfiles[0]['rol'] != 'admin':
        await db.request('PATCH','perfiles',params={'id':'eq.' + user_id},data={'rol':'admin'})
    return user_id


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aplicar', action='store_true')
    parser.add_argument('--empresa', default='neifit')
    parser.add_argument('--administrador', help='Cuenta administradora existente; evita crear admin@neifit.com')
    parser.add_argument('--crear-usuarios-demo', action='store_true')
    args = parser.parse_args()
    if not args.aplicar:
        print('PREVISUALIZACIÓN: empresa neifit, 13 productos, 3 cotizaciones, 3 pedidos y 2 pagos simulados.')
        print('Usuarios demo opcionales: admin, mensajería y cliente. No se muestran ni almacenan contraseñas.')
        return
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError('Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en backend/.env')

    async with httpx.AsyncClient(timeout=30) as client:
        db.client = client
        empresas = await db.rows('empresas', {'slug':'eq.' + args.empresa, 'estado':'eq.activa', 'select':'id,slug'})
        if len(empresas) != 1:
            raise RuntimeError('Empresa activa no encontrada: ' + args.empresa)
        empresa_id = empresas[0]['id']

        usuarios = {}
        if args.administrador:
            email = args.administrador.strip().lower()
            usuarios['admin'] = await asegurar_usuario(client,empresa_id,email,'Administrador','admin','',False)
        else:
            email,nombre,rol,variable = USUARIOS[0]
            usuarios['admin'] = await asegurar_usuario(client,empresa_id,email,nombre,rol,variable,args.crear_usuarios_demo)
        if args.crear_usuarios_demo:
            for email,nombre,rol,variable in USUARIOS[1:]:
                usuarios[rol] = await asegurar_usuario(client,empresa_id,email,nombre,rol,variable,True)
        actor = usuarios['admin']

        filas_categorias = await db.rows('categorias', {
            'empresa_id':'eq.' + empresa_id, 'activo':'eq.true',
            'select':'id,slug:identificador_url'})
        categorias = {row['slug']:row['id'] for row in filas_categorias}
        if not {'postres','snacks','bebidas'}.issubset(categorias):
            raise RuntimeError('Faltan las categorías postres, snacks y bebidas de Neifit')
        imagenes_categorias = {
            'postres':'/images/postre-maracuya.png',
            'snacks':'/images/cocadas.png',
            'bebidas':'/images/bebidas-ilustrativas.png',
        }
        for slug, imagen in imagenes_categorias.items():
            await db.request('PATCH','categorias',params={
                'id':'eq.' + categorias[slug], 'empresa_id':'eq.' + empresa_id},
                data={'url_imagen':imagen})

        ids = {}
        manifiesto = {'tipo':'Datos inventados para demostración; pagos simulados sin fondos reales.',
                      'empresa':args.empresa,'usuarios':[], 'productos':[], 'cotizaciones':[], 'pedidos':[]}
        for email,_,rol,_ in USUARIOS:
            if rol in usuarios: manifiesto['usuarios'].append({'email':email,'rol':rol,'id':usuarios[rol]})
        for index,(nombre,slug,categoria,precio,existencias,imagen,descripcion) in enumerate(PRODUCTOS):
            print(f'Producto {index + 1}/13: {nombre}')
            slug_demo = 'prueba-' + slug
            existentes = await db.rows('productos', {'empresa_id':'eq.' + empresa_id,
                'identificador_url':'eq.' + slug_demo,'select':'id,nombre,precio,existencias'})
            if existentes:
                producto = existentes[0]
            else:
                producto = await db.rpc('neifit_guardar_producto',p_actor=actor,p_empresa=empresa_id,p_id=None,p_datos={
                    'nombre':nombre,'identificador_url':slug_demo,'categoria_id':categorias[categoria],
                    'descripcion':descripcion,'precio':precio,'existencias':existencias,'activo':True,
                    'disponible':True,'destacado':index<3,'url_imagen':'/images/'+imagen+'.png'})
            ids[slug] = producto['id']
            manifiesto['productos'].append({'id':producto['id'],'nombre':nombre,'precio':precio})

        items_cotizacion = [[('postre-maracuya',1),('mousse-mango',1),('postre-fresa',1)],
            [('cocadas',10),('datiles-mani',5)],[('bebida-tropical-1',2),('mix-frutos-secos',2)]]
        notas_cotizacion = ['Cotización para refrigerios de una reunión empresarial.',
            'Solicitud de snacks para compartir en oficina.','Selección de bebidas para un evento interno.']
        for indice,items in enumerate(items_cotizacion,1):
            print(f'Cotización {indice}/3')
            cliente = CLIENTES[indice-1]
            cotizacion = await db.rpc('neifit_crear_documento',p_actor=actor,p_empresa=empresa_id,
                p_tipo='quote',p_solicitud=str(uuid5(NAMESPACE_URL,f'neifit-es/{empresa_id}/{actor}/cotizacion/{indice}')),
                p_datos={**{k:v for k,v in cliente.items() if k!='direccion'},'notas':notas_cotizacion[indice-1],
                    'items':[{'producto_id':ids[k],'cantidad':n} for k,n in items]})
            if indice == 3 and cotizacion['estado'] == 'pendiente':
                cotizacion = await db.rpc('neifit_actualizar_cotizacion',p_actor=actor,p_empresa=empresa_id,
                    p_id=cotizacion['id'],p_estado='respondida')
            manifiesto['cotizaciones'].append({'id':cotizacion['id'],'numero':cotizacion['numero_cotizacion'],
                'estado':cotizacion['estado'],'cliente':cliente['nombre_cliente']})

        items_pedido = [[('postre-maracuya',1),('mousse-mango',2)],[('postre-fresa',3)],
            [('cocadas',5),('datiles-mani',2)]]
        notas_pedido = ['Entregar en recepción.','Confirmar entrega con portería.','Empacar los productos por separado.']
        for indice,items in enumerate(items_pedido,1):
            print(f'Pedido {indice}/3')
            cliente = CLIENTES[indice-1]
            parametros = {'p_actor':actor,'p_empresa':empresa_id,'p_tipo':'order',
                'p_solicitud':str(uuid5(NAMESPACE_URL,f'neifit-es/{empresa_id}/{actor}/pedido/{indice}')),
                'p_datos':{**cliente,'notas':notas_pedido[indice-1],'metodo_pago':'contraentrega',
                    'items':[{'producto_id':ids[k],'cantidad':n} for k,n in items]}}
            try:
                pedido = await db.rpc('neifit_crear_documento', **parametros)
            except Exception:
                diagnostico = await client.post(settings.SUPABASE_URL.rstrip('/') +
                    '/rest/v1/rpc/neifit_crear_documento',headers=service_headers(
                    settings.SUPABASE_SERVICE_ROLE_KEY),json=parametros)
                error = diagnostico.json() if diagnostico.content else {}
                raise RuntimeError(f"{error.get('code','RPC')}: {error.get('message','Pedido rechazado')}") from None
            print('  documento creado o recuperado')
            if indice <= 2 and not pedido.get('usuario_mensajero_asignado_id'):
                asignacion = {'p_actor':actor,'p_empresa':empresa_id,'p_id':pedido['id'],'p_mensajero':actor}
                try:
                    pedido = await db.rpc('neifit_asignar_mensajero',**asignacion)
                except Exception:
                    diagnostico = await client.post(settings.SUPABASE_URL.rstrip('/') +
                        '/rest/v1/rpc/neifit_asignar_mensajero',headers=service_headers(
                        settings.SUPABASE_SERVICE_ROLE_KEY),json=asignacion)
                    error = diagnostico.json() if diagnostico.content else {}
                    raise RuntimeError(f"{error.get('code','RPC')}: {error.get('message','Asignación rechazada')}") from None
            print('  asignación verificada')
            if indice == 2 and pedido['estado_pedido'] == 'recibido':
                pedido = await db.rpc('neifit_actualizar_pedido',p_actor=actor,p_empresa=empresa_id,
                    p_id=pedido['id'],p_estado='en_preparacion',p_mensaje='Productos en preparación.')
            print('  estado verificado')
            if indice <= 2:
                pedido = await db.rpc('neifit_registrar_pago_simulado',p_actor=actor,
                    p_empresa=empresa_id,p_id=pedido['id'])
                print('  transacción simulada verificada')
                print('  estado de pago actualizado')
            manifiesto['pedidos'].append({'id':pedido['id'],'numero':pedido['numero_pedido'],
                'estado':pedido['estado_pedido'],'pago':pedido['estado_pago'],'total':pedido['total'],
                'cliente':cliente['nombre_cliente'],'pago_simulado':indice<=2})

        salida = ROOT / 'supabase/datos_demo_espanol_creados.json'
        salida.write_text(json.dumps(manifiesto,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Carga completa: 13 productos, 3 cotizaciones, 3 pedidos y 2 pagos simulados.')
        print('Manifiesto local:', salida)
        db.client = None


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as error:
        from fastapi import HTTPException
        print('Carga detenida:', error.detail if isinstance(error,HTTPException) else str(error))
        raise SystemExit(1)

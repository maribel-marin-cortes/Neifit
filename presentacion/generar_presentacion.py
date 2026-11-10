"""Genera la presentación local de Neifit. No lee .env ni utiliza servicios remotos.
Ejecutar: uv run --no-project --with python-pptx python presentacion/generar_presentacion.py
"""
from pathlib import Path
import base64
import html
import json
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.xmlchemy import OxmlElement
from consultas_presentacion import CONSULTAS

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
LOGO = ROOT / 'frontend/public/logo-neifit-tropical.png'
CREAM, BROWN, GREEN, PINK, WHITE = 'F6E7D8', '4B2E1F', '5F8D4E', 'D98CA4', 'FFF8F2'

SLIDES = [
 dict(kind='cover', tag='PRESENTACIÓN DEL PROYECTO', title='Neifit', subtitle='Sabores tradicionales.\nUna experiencia digital cercana.',
      cards=[('Tienda virtual', 'Postres · Snacks · Bebidas'), ('Integrantes', 'Maribel Marín Cortés\nNixon Garcia\nFlor Neifix González')],
      note='Buenos días. Somos Maribel Marín Cortés, Nixon Garcia y Flor Neifix González, y presentamos Neifit: una tienda virtual para organizar la oferta de postres, snacks y bebidas. El proyecto conecta la experiencia de compra del cliente con la gestión administrativa y el seguimiento de entregas. Vamos a explicar la necesidad, los usuarios, el modelo de datos y el estado actual del desarrollo.'),
 dict(kind='cards', tag='01 / LA NECESIDAD', title='Una venta necesita más que un mensaje.', subtitle='El problema que busca resolver Neifit',
      cards=[('Información dispersa', 'Solicitudes, datos del cliente y productos en registros separados.'), ('Poco control', 'Dificultad para conocer cantidades, disponibilidad y solicitudes pendientes.'), ('Seguimiento limitado', 'El cliente necesita saber qué ocurrió con su pedido y su entrega.')],
      takeaway='Centralizar la información para atender, organizar y dar seguimiento.',
      note='La necesidad es organizar el proceso comercial en un solo sistema. Cuando las solicitudes se manejan de forma dispersa, puede ser difícil identificar qué pidió cada cliente, qué solicitudes están pendientes y cómo avanza una entrega. Estos son los problemas que el proyecto busca solucionar; no son resultados de una encuesta ni estadísticas medidas de la empresa.'),
 dict(kind='flow', tag='02 / LA SOLUCIÓN', title='De conocer la marca a recibir el pedido.', subtitle='Una plataforma web con acceso según la función de cada persona',
      cards=[('01 · Explorar', 'Landing institucional y muestra de productos.'), ('02 · Ingresar', 'Registro e inicio de sesión con Supabase Auth.'), ('03 · Solicitar', 'Carrito, pedido o cotización según la necesidad.'), ('04 · Gestionar', 'Administración y seguimiento de la entrega.')],
      takeaway='React + Vite → FastAPI → Supabase / PostgreSQL: arquitectura objetivo.',
      note='El recorrido empieza en una página pública donde el visitante conoce la empresa. Para acceder a los módulos comerciales se requiere iniciar sesión. El cliente puede comprar o cotizar; el administrador consulta las solicitudes; y el mensajero gestiona sus entregas asignadas. React y Vite construyen la interfaz, FastAPI aplica las reglas y Supabase aporta autenticación y la base de datos diseñada. La integración persistente de pedidos y cotizaciones todavía está pendiente.'),
 dict(kind='cards', tag='03 / BENEFICIARIOS', title='Una plataforma. Responsabilidades distintas.', subtitle='¿Quiénes la utilizarían?',
      cards=[('Cliente', 'Consulta productos, solicita cotizaciones, crea pedidos y consulta los propios.'), ('Administrador', 'Gestiona productos, solicitudes, usuarios, roles y permisos.'), ('Mensajero', 'Consulta entregas asignadas y registra avances o novedades.')],
      takeaway='Los roles personalizados amplían las funciones mediante permisos autorizados.',
      note='Los actores principales son el cliente, el administrador y el mensajero. Cada uno necesita información diferente. Un cliente no debe ver pedidos ajenos y un mensajero no debe administrar usuarios. La ampliación de roles personalizados permite autorizar funciones como inventario sin otorgar toda la administración. Esta gestión requiere las migraciones y la configuración descritas en el proyecto.'),
 dict(kind='cards', tag='04 / INFORMACIÓN', title='¿Qué necesita conocer el sistema?', subtitle='La información se organiza en cuatro grupos',
      cards=[('Personas y acceso', 'Nombre, correo, teléfono, rol y permisos.'), ('Catálogo', 'Categorías, productos, precios, ingredientes, alérgenos y stock.'), ('Operación', 'Carritos, pedidos, cotizaciones, detalles y direcciones.'), ('Control', 'Seguimiento, transacciones de pago y auditoría de accesos.')],
      takeaway='Las contraseñas se administran en Supabase Auth, no en profiles.',
      note='El sistema maneja información de personas, productos, operaciones y control. También contempla el contenido institucional, como misión, valores y datos de contacto. Una decisión importante es no guardar contraseñas en la tabla de perfiles: la autenticación corresponde a Supabase Auth. La tabla de perfiles conserva la información necesaria para la operación y la autorización.'),
 dict(kind='table', tag='05 / ENTIDADES Y ATRIBUTOS', title='La base del modelo.', subtitle='Entidades principales del catálogo y de los usuarios',
      headers=['Entidad', 'Atributos principales', 'Función'],
      rows=[['profiles', 'id, full_name, email, phone, role', 'Identidad operativa del usuario'], ['categories', 'id, name, slug, is_active', 'Agrupar productos'], ['products', 'id, category_id, name, price, stock, image_url', 'Describir la oferta y su disponibilidad'], ['carts / cart_items', 'user_id, status / product_id, quantity, unit_price', 'Organizar la intención de compra']],
      takeaway='Cada registro tiene identidad propia y referencias a las entidades relacionadas.',
      note='La tabla profiles se vincula con auth.users. Las categorías agrupan los productos, y cada producto pertenece a una categoría. El producto incluye precio y stock, además de información descriptiva. El carrito se separa de sus detalles para que pueda contener varios productos sin repetir todos los datos del usuario. Los atributos mostrados son un resumen del SQL, no la lista completa de columnas.'),
 dict(kind='table', tag='06 / ENTIDADES Y ATRIBUTOS', title='Cada solicitud conserva su detalle.', subtitle='Entidades transaccionales del modelo diseñado',
      headers=['Entidad', 'Atributos principales', 'Función'],
      rows=[['orders', 'id, user_id, order_number, address, order_status, total', 'Registrar una compra'], ['order_items', 'order_id, product_id, product_name, quantity, unit_price', 'Conservar los productos y precios del pedido'], ['quotes / quote_items', 'quote_number, user_id, status / quantity, reference_price', 'Registrar una solicitud de cotización'], ['order_tracking', 'order_id, status, message, updated_by, created_at', 'Conservar el historial de entrega'], ['payment_transactions', 'order_id, provider, amount, status, provider_reference', 'Registrar intentos o resultados de pago']],
      takeaway='Una cotización expresa interés comercial; un pedido registra la compra.',
      note='Los pedidos y las cotizaciones son entidades diferentes porque representan momentos distintos del proceso comercial. Sus detalles resuelven la relación con los productos. El detalle de un pedido conserva el nombre y el precio de la compra aunque el catálogo cambie después. El seguimiento conserva eventos en el tiempo. Las transacciones de pago están contempladas en el esquema, pero no se presenta una pasarela real como terminada.'),
 dict(kind='diagram', tag='07 / RELACIONES', title='Las relaciones dan coherencia al negocio.', subtitle='Esquema conceptual simplificado · 1 = uno · N = muchos',
      note='Un usuario puede tener muchos pedidos y cotizaciones. Un pedido tiene muchos detalles; cada detalle referencia un producto. De manera similar, una cotización contiene varios detalles. Una categoría tiene muchos productos. El pedido también puede tener muchos eventos de seguimiento y transacciones de pago. La asignación del mensajero es otra relación con profiles, distinta del cliente que hizo la compra. El diagrama resume las relaciones principales y no todas las tablas del esquema.'),
 dict(kind='table', tag='08 / ROLES Y PERMISOS', title='El acceso depende de lo autorizado.', subtitle='Permisos con nombres concretos para cada responsabilidad',
      headers=['Módulo o acción', 'Permiso', 'Alcance'],
      rows=[['Catálogo', 'catalog.read', 'Consultar productos'], ['Pedidos propios', 'orders.read_own', 'Solo registros del cliente'], ['Entregas asignadas', 'delivery.read_assigned', 'Solo pedidos asignados'], ['Productos e inventario', 'products.manage', 'Gestión autorizada'], ['Usuarios / Roles', 'users.manage / access.manage', 'Reservados al administrador']],
      takeaway='access_roles ↔ role_permissions ↔ permissions · La API verifica el acceso.',
      note='Los usuarios tienen un rol y los permisos se asignan al rol. access_roles define los roles; permissions identifica las acciones; y role_permissions relaciona ambos. También se incluyen límites delegables y auditoría de cambios. Ocultar una opción del menú mejora la experiencia, pero no garantiza seguridad: FastAPI valida permisos y propiedad en cada operación. La gestión de usuarios y de roles está reservada al administrador.'),
 dict(kind='cards', tag='09 / RESTRICCIONES', title='Reglas que protegen la información.', subtitle='Integridad de datos y autorización',
      cards=[('Datos válidos', 'Precios y cantidades positivos. Stock no negativo. Estados permitidos.'), ('Referencias consistentes', 'Claves primarias y foráneas. Números de pedido y cotización únicos.'), ('Compras coherentes', 'Un carrito activo por usuario. Un producto por detalle de cada documento.'), ('Acceso controlado', 'RLS en tablas privadas. Sin cambio del rol propio. Entregas por asignación.')],
      takeaway='En el SQL, los subtotales de detalle y el total del pedido son columnas calculadas.',
      note='Las restricciones evitan valores imposibles, duplicaciones y referencias inexistentes. Las claves foráneas conectan las tablas; los valores únicos identifican documentos; y las restricciones check limitan estados y cantidades. También se consideran reglas de autorización y RLS. La validación transaccional de stock y totales desde el servidor debe completarse junto con la persistencia comercial; no basta con comprobar que un valor sea positivo.'),
 dict(kind='cards', tag='10 / DECISIONES DE DISEÑO', title='Un modelo relacional para crecer con orden.', subtitle='¿Por qué se diseñó de esta manera?',
      cards=[('Separar responsabilidades', 'Usuarios, productos, documentos y detalles tienen funciones distintas.'), ('Conservar el contexto', 'El precio del pedido no cambia cuando cambia el catálogo.'), ('Mantener trazabilidad', 'Cada avance de entrega y cambio de acceso puede quedar registrado.')],
      takeaway='Menos duplicación innecesaria, mejores relaciones y consultas más claras.',
      note='El modelo relacional se ajusta a un negocio con relaciones claras y necesidad de consistencia. Separar los detalles de las cabeceras facilita manejar varios productos por solicitud. Guardar ciertos datos históricos en el pedido es una duplicación deliberada: permite conservar el contexto de la compra. Además, separar transacciones de pago admite varios intentos para un mismo pedido. El diseño busca crecer sin mezclar las responsabilidades de cada entidad.'),
 dict(kind='queries', tag='11 / CONSULTAS ÚTILES', title='De los registros a decisiones útiles.', subtitle='Ejemplos sobre las tablas del modelo, cuando tengan datos persistidos',
      cards=[('Inventario bajo', '¿Qué productos necesitan reposición?'), ('Solicitudes pendientes', '¿Qué cotizaciones faltan por atender?'), ('Operación de entregas', '¿Qué pedidos siguen sin entregar?')],
      sql="SELECT name, stock\nFROM public.products\nWHERE is_active = true AND stock <= 5\nORDER BY stock ASC;",
      takeaway='También: productos más vendidos, pedidos por mensajero y ventas con pago aprobado.',
      note='La base de datos permite responder preguntas operativas. Este ejemplo consulta productos activos con cinco o menos unidades. Otras consultas pueden sumar las cantidades de productos vendidos en pedidos con pago aprobado, identificar cotizaciones pendientes o agrupar entregas por mensajero. Son consultas propuestas sobre el esquema diseñado: sus resultados dependen de que los módulos realmente guarden datos en PostgreSQL. El archivo consultas_ejemplo.sql incluye ejemplos adicionales.'),
 dict(kind='status', tag='12 / ESTADO DEL PROYECTO', title='Prototipo funcional, con una ruta de evolución.', subtitle='Diferenciar lo implementado de lo pendiente',
      cards=[('Implementado en el código', 'Interfaz y módulos comerciales. Autenticación con Supabase. Controles de acceso en la API. Gestión de roles preparada con SQL y configuración.'), ('Pendiente para producción', 'Persistir pedidos y cotizaciones en Supabase. Validar stock y totales con transacciones. Integrar y verificar pagos reales. Completar pruebas de operación.')],
      takeaway='Hoy los pedidos y las cotizaciones siguen en memoria y se pierden al reiniciar el backend.',
      note='Es importante explicar el estado real. Existe una interfaz funcional y controles de acceso, así como un esquema SQL para la base de datos. La gestión persistente de roles requiere aplicar sus migraciones y activar la configuración; no se asegura aquí que estén instaladas en la instancia. Los servicios comerciales de pedidos y cotizaciones todavía almacenan datos en memoria. La siguiente prioridad es la persistencia transaccional, seguida por pagos reales y validación completa de la operación.'),
 dict(kind='closing', tag='CIERRE / SIGUIENTE PASO', title='Organizar la venta.\nAcompañar cada entrega.', subtitle='Neifit conecta clientes, administración y mensajería en una misma experiencia.',
      cards=[('1 · Demostrar', 'Recorrer catálogo, cotización y panel administrativo.'), ('2 · Consolidar', 'Conectar los documentos comerciales a PostgreSQL.'), ('3 · Validar', 'Comprobar permisos, inventario y pagos de extremo a extremo.')],
      takeaway='Gracias · Preguntas',
      note='Para cerrar, Neifit propone una experiencia de compra cercana y una operación más organizada. En una demostración puedo recorrer la landing, el catálogo y la solicitud de cotización, y después mostrar el panel administrativo con una cuenta autorizada. Debo mantener el backend encendido y no prometer que los datos sobreviven a un reinicio. Los siguientes pasos son consolidar persistencia y transacciones, integrar pagos y validar la operación completa. Muchas gracias. Quedo atenta a sus preguntas.'),
]


query_index = next(i for i, slide in enumerate(SLIDES) if slide['kind'] == 'queries')
SLIDES[query_index:query_index+1] = [
    dict(kind='queries', tag=f'11 / CONSULTAS SQL · {i+1} DE {len(CONSULTAS)}',
         title=title, subtitle=purpose,
         cards=[(topic, explanation), ('Datos requeridos', 'Tablas instaladas y registros persistidos en PostgreSQL.')],
         sql=sql, takeaway='Consulta de solo lectura · Ejecutar con autorización administrativa.',
         note=f'{purpose} {explanation} Esta consulta utiliza SQL de PostgreSQL. Los resultados dependen de los datos realmente guardados en la base de datos; no recupera registros que solo existían en memoria.')
    for i, (title, purpose, topic, explanation, sql) in enumerate(CONSULTAS)
]


def esc(value):
    return html.escape(value).replace('\n', '<br>')


def relationship_svg():
    nodes = [('Categorías', 25, 40), ('Productos', 345, 40), ('Detalles de pedido', 665, 40),
             ('Usuarios', 25, 210), ('Pedidos', 345, 210), ('Seguimiento', 665, 210),
             ('Cotizaciones', 25, 380), ('Detalles de cotización', 345, 380), ('Transacciones de pago', 665, 380)]
    edges = [(245, 80, 345, 80, '1 : N'), (565, 80, 665, 80, '1 : N'),
             (245, 250, 345, 250, '1 : N'), (565, 250, 665, 250, '1 : N'),
             (135, 290, 135, 380, '1 : N'), (245, 420, 345, 420, '1 : N'),
             (455, 290, 775, 380, '1 : N'), (455, 210, 775, 120, '1 : N')]
    s = '<svg viewBox="0 0 940 490" role="img" aria-label="Relaciones principales: categorías, productos, usuarios, pedidos, cotizaciones, detalles, seguimiento y pagos"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#5F8D4E"/></marker></defs>'
    for x1,y1,x2,y2,label in edges:
        s += f'<g><path d="M{x1},{y1} L{x2},{y2}" stroke="#5F8D4E" stroke-width="2" fill="none" marker-end="url(#arrow)"/><text x="{(x1+x2)/2+7}" y="{(y1+y2)/2-9}" fill="#4B2E1F" font-size="15">{label}</text></g>'
    for title,x,y in nodes:
        s += f'<g><rect x="{x}" y="{y}" width="220" height="80" rx="15" fill="#FFF8F2" stroke="#D7C4B4"/><text x="{x+110}" y="{y+46}" text-anchor="middle" font-size="17" fill="#4B2E1F" font-family="Segoe UI,Arial">{title}</text></g>'
    return s + '</svg>'


def make_html():
    encoded = base64.b64encode(LOGO.read_bytes()).decode()
    pages = []
    for i, slide in enumerate(SLIDES):
        cards = ''.join(f'<article class="card reveal"><span class="number">{j+1:02}</span><h3>{esc(title)}</h3><p>{esc(body)}</p></article>' for j,(title,body) in enumerate(slide.get('cards', [])))
        if slide['kind'] == 'cover':
            body = f'<div class="cover-copy"><h1>{slide["title"]}</h1><p class="cover-sub">{esc(slide["subtitle"])}</p><div class="cover-meta">{cards}</div></div><div class="logo-frame reveal"><img src="data:image/png;base64,{encoded}" alt="Logo Neifit"/></div>'
        else:
            body = f'<header><h2>{esc(slide["title"])}</h2><p class="subtitle">{esc(slide["subtitle"])}</p></header>'
            if slide['kind'] == 'table':
                body += '<table class="reveal"><thead><tr>' + ''.join(f'<th>{esc(h)}</th>' for h in slide['headers']) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join(f'<td>{esc(c)}</td>' for c in row)+'</tr>' for row in slide['rows'])+'</tbody></table>'
            elif slide['kind'] == 'diagram':
                body += '<div class="diagram reveal">'+relationship_svg()+'</div>'
            elif slide['kind'] == 'queries':
                body += f'<div class="query-layout"><div class="cards">{cards}</div><pre class="reveal"><span>SQL / POSTGRESQL</span><code>{html.escape(slide["sql"])}</code></pre></div>'
            else:
                body += f'<div class="cards count-{len(slide.get("cards", []))}">{cards}</div>'
            if slide.get('takeaway'):
                body += f'<p class="takeaway reveal">{esc(slide["takeaway"])}</p>'
        pages.append(f'<section class="slide kind-{slide["kind"]} {"active" if i == 0 else ""}" data-index="{i}" aria-label="Diapositiva {i+1}: {html.escape(slide["title"])}"><div class="topline"><span>{slide["tag"]}</span><span>NEIFIT / PROYECTO WEB</span></div><div class="slide-content">{body}</div><footer><span>NEIFIT · PRESENTACIÓN DEL PROYECTO · 10 NOV 2026</span><span>{i+1:02} / {len(SLIDES):02}</span></footer></section>')
    template = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Neifit · Presentación del proyecto</title>
<style>
:root{--cream:#F6E7D8;--brown:#4B2E1F;--green:#5F8D4E;--white:#FFF8F2;--pink:#D98CA4}*{box-sizing:border-box}body{margin:0;background:#211b17;color:var(--brown);font-family:'Segoe UI',Arial,sans-serif;overflow:hidden}.viewport{position:fixed;inset:0 0 64px;display:grid;place-items:center}.deck{width:1280px;height:720px;flex:none;position:relative;transform-origin:center center}.slide{position:absolute;inset:0;background:var(--cream);padding:35px 62px 30px;display:none;overflow:hidden;border-top:7px solid var(--green)}.slide.active{display:flex;flex-direction:column;animation:pageIn .55s ease both}.slide:after{content:'';position:absolute;width:340px;height:340px;border-radius:50%;background:#5f8d4e09;right:-150px;top:-150px;pointer-events:none}.topline{display:flex;justify-content:space-between;font-size:12px;font-weight:700;letter-spacing:2px;color:var(--green);margin-bottom:25px}.slide-content{flex:1;min-height:0;display:flex;flex-direction:column;position:relative;z-index:1}header{margin-bottom:23px}h1,h2,h3,p{margin:0}h1{font:italic 122px Georgia,serif;letter-spacing:-7px}h2{font:normal 47px/1.08 Georgia,serif;letter-spacing:-1.3px;max-width:1090px}.subtitle{font-size:20px;margin-top:14px;color:#7A5B47}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;flex:1;align-content:center}.count-4{grid-template-columns:repeat(2,1fr)}.count-2{grid-template-columns:repeat(2,1fr)}.card{background:var(--white);border:1px solid #4b2e1f12;border-radius:19px;padding:26px;min-width:0;box-shadow:0 7px 18px #4b2e1f06}.number{display:block;font:italic 36px Georgia,serif;color:var(--green);margin-bottom:16px}h3{font-size:25px;font-weight:650;line-height:1.18;margin-bottom:14px}.card p{font-size:21px;line-height:1.43;color:#705540}.count-4 .card{padding:21px 25px}.count-4 .number{float:right;margin:0 0 10px 15px;font-size:28px}.count-4 h3{font-size:24px}.count-4 p{font-size:20px}.takeaway{background:#5f8d4e14;border-left:4px solid var(--green);padding:15px 19px;margin-top:22px;font-size:19px;line-height:1.35;font-weight:600;border-radius:0 10px 10px 0}footer{display:flex;justify-content:space-between;border-top:1px solid #4b2e1f22;padding-top:15px;font-size:11px;letter-spacing:1.5px;margin-top:22px;color:#856954}.cover{background:linear-gradient(120deg,#f6e7d8 65%,#e4e9d4 65%)}.cover .slide-content{flex-direction:row;align-items:center;gap:60px}.cover-copy{width:57%}.cover-sub{font-size:31px;line-height:1.32;margin:16px 0 34px}.cover-meta{display:flex;gap:25px}.cover-meta .card{padding:0;background:none;box-shadow:none;border:0}.cover-meta .number{display:none}.cover-meta h3{font-size:17px;color:var(--green);margin-bottom:7px}.cover-meta p{font-size:16px}.logo-frame{width:360px;padding:15px;background:var(--white);border-radius:30px;box-shadow:0 22px 65px #4b2e1f18;transform:rotate(-3deg)}.logo-frame img{display:block;width:100%;height:auto;border-radius:16px}.flow .cards{grid-template-columns:repeat(4,1fr);gap:15px}.flow .card{padding:23px}.flow h3{font-size:24px}.flow .card p{font-size:20px}.flow .number{font-size:46px}.diagram{width:100%;flex:1;min-height:0;display:grid;place-items:center}.diagram svg{height:100%;max-width:100%}.diagram~.takeaway{display:none}table{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border:1px solid #4b2e1f20;border-radius:15px;font-size:18px;line-height:1.3;background:var(--white);margin:auto 0}th{background:var(--green);color:white;text-align:left;padding:15px 17px;font-weight:600}td{padding:16px 17px;border-bottom:1px solid #4b2e1f12;vertical-align:middle}tr:last-child td{border:0}td:first-child{font-weight:650;width:23%}td:nth-child(2){width:43%;font-size:17px}td:nth-child(3){width:34%}.table .takeaway{font-size:18px}.query-layout{display:grid;grid-template-columns:37% 1fr;gap:28px;flex:1;align-items:center}.query-layout .cards{display:flex;flex-direction:column;gap:12px}.queries .card{padding:15px 20px}.queries .number{display:none}.queries h3{font-size:22px;margin-bottom:6px}.queries .card p{font-size:18px}.queries pre{background:#30251e;color:#f4ebdd;padding:30px 24px;border-radius:20px;font-size:20px;line-height:1.8;white-space:pre-wrap;margin:0}.queries pre span{display:block;color:#aac596;font-size:12px;letter-spacing:2px;margin-bottom:20px}.status .card:nth-child(2){background:#f8e4df}.status .takeaway{background:#f8e4df;border-color:#a55e3d}.closing{background:#e6ead8}.closing h2{font-size:61px;max-width:900px}.closing .subtitle{max-width:900px}.closing .cards{gap:17px}.closing .card{padding:20px}.closing .number{display:none}.closing h3{font-size:22px}.closing .card p{font-size:19px}.closing .takeaway{text-align:center;background:var(--green);color:white;border:0;font-size:25px}
.active .reveal{animation:riseIn .55s ease both}.active .reveal:nth-child(2){animation-delay:.13s}.active .reveal:nth-child(3){animation-delay:.26s}.active .reveal:nth-child(4){animation-delay:.39s}@keyframes pageIn{from{opacity:.3}to{opacity:1}}@keyframes riseIn{from{opacity:0;translate:0 18px}to{opacity:1;translate:0 0}}.controls{position:fixed;bottom:0;left:0;right:0;height:64px;display:flex;align-items:center;justify-content:center;gap:11px;background:#211b17;color:#f6e7d8;padding:8px 15px;font-size:13px}button{font:inherit;cursor:pointer;border:1px solid #ffffff30;background:#ffffff0c;color:inherit;padding:9px 14px;border-radius:9px}button:hover{background:#ffffff20}button:focus-visible{outline:3px solid #d98ca4;outline-offset:2px}button:disabled{opacity:.35;cursor:default}.counter{min-width:55px;text-align:center}.timer{font-variant-numeric:tabular-nums;color:#b8cba8;padding:0 10px}.progress{position:fixed;bottom:64px;left:0;height:3px;background:#d98ca4;transition:width .3s}.notes{position:fixed;right:22px;bottom:84px;width:min(650px,calc(100vw - 44px));background:#fff8f2;color:#4b2e1f;border:2px solid #5f8d4e;border-radius:18px;padding:22px 26px;box-shadow:0 18px 90px #0005;line-height:1.65;font-size:18px;z-index:20;max-height:60vh;overflow:auto}.notes h3{font-size:17px;color:#5f8d4e}.notes[hidden],.overview[hidden]{display:none}.overview{position:fixed;inset:0;background:#211b17f5;z-index:30;overflow:auto;padding:35px;color:#f6e7d8}.overview-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:15px;max-width:1100px;margin:30px auto}.overview button{text-align:left;min-height:110px;padding:19px;font-size:18px}.overview button span{display:block;color:#b8cba8;font-size:12px;margin-bottom:12px}.help{color:#d7bfa9}.presenting .controls{opacity:0;transition:opacity .2s}.presenting .controls:hover,.presenting .controls:focus-within{opacity:1}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}@media(max-width:650px){.help,.timer{display:none}.controls{gap:5px}.controls button{padding:9px;font-size:12px}}
@page{size:13.333333in 7.5in;margin:0}@media print{html,body{margin:0;padding:0;width:1280px;height:auto;background:white;overflow:visible;-webkit-print-color-adjust:exact;print-color-adjust:exact}.viewport{position:static;display:block;width:1280px;height:auto}.deck{width:1280px;height:auto;transform:none!important}.slide,.slide.active{display:flex!important;position:relative!important;width:1280px;height:720px;break-after:page;page-break-after:always;animation:none!important}.slide:last-child{break-after:auto;page-break-after:auto}.reveal{opacity:1!important;animation:none!important}.controls,.notes,.overview,.progress{display:none!important}.logo-frame{transform:rotate(-3deg)}}
</style></head><body>
<div class="viewport"><main class="deck" id="deck">__SLIDES__</main></div>
<div class="progress" id="progress"></div>
<nav class="controls" aria-label="Controles de presentación"><button id="prev" aria-label="Diapositiva anterior">←</button><span class="counter" id="counter"></span><button id="next" aria-label="Diapositiva siguiente">→</button><button id="fullscreen">Pantalla completa · F</button><button id="notesButton" aria-expanded="false">Guion · N</button><button id="overviewButton">Índice · O</button><details class="downloads"><summary>Descargar ↓</summary><div><button type="button" id="downloadHtml">Presentación animada · HTML</button><a href="Neifit_presentacion_consultas.pptx" download>PowerPoint editable · PPTX</a><a href="Neifit_presentacion_consultas.pdf" download>Presentación · PDF</a><a href="Neifit_paquete_consultas.zip" download>Paquete completo · ZIP</a></div></details><span class="timer" id="timer">00:00</span><span class="help">← → / espacio para avanzar</span></nav>
<style>.downloads{position:relative}.downloads summary{cursor:pointer;list-style:none;border:1px solid #ffffff30;background:#ffffff0c;border-radius:9px;padding:9px 14px;white-space:nowrap}.downloads summary:focus-visible{outline:3px solid #d98ca4;outline-offset:2px}.downloads>div{position:absolute;bottom:49px;right:0;width:280px;padding:9px;background:#30251e;border:1px solid #d7bfa955;border-radius:13px;box-shadow:0 10px 35px #0006}.downloads a,.downloads>div button{display:block;text-align:left;color:#f6e7d8;text-decoration:none;width:100%;padding:13px 11px;border:0;background:transparent;border-radius:7px;font:inherit}.downloads a:hover,.downloads>div button:hover{background:#ffffff18}@media(max-width:650px){.controls{gap:3px}.controls #fullscreen{display:none}.downloads summary{padding:9px}}</style>
<aside class="notes" id="notes" hidden><h3>Guion de apoyo · solo para ti</h3><p id="noteText"></p></aside>
<div class="overview" id="overview" hidden><button id="closeOverview">Cerrar índice · Esc</button><div class="overview-grid" id="overviewGrid"></div></div>
<script>
const data=__DATA__;const slides=[...document.querySelectorAll('.slide')];const deck=document.getElementById('deck');let current=0;const notes=document.getElementById('notes');const overview=document.getElementById('overview');let start=Date.now();
document.getElementById('downloadHtml').onclick=()=>{document.querySelector('.downloads').open=false;const copy=document.documentElement.cloneNode(true);copy.querySelector('#notes').hidden=true;copy.querySelector('#overview').hidden=true;const blob=new Blob(['<!doctype html>\n'+copy.outerHTML],{type:'text/html;charset=utf-8'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='Neifit_presentacion_animada.html';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000)};
function resize(){deck.style.transform=`scale(${Math.min(innerWidth/1280,(innerHeight-70)/720)})`}window.addEventListener('resize',resize);resize();
function show(index){current=Math.max(0,Math.min(slides.length-1,index));slides.forEach((s,i)=>{s.classList.toggle('active',i===current);s.setAttribute('aria-hidden',String(i!==current))});document.getElementById('counter').textContent=`${current+1} / ${slides.length}`;document.getElementById('progress').style.width=`${(current+1)/slides.length*100}%`;document.getElementById('noteText').textContent=data[current].note;document.getElementById('prev').disabled=current===0;document.getElementById('next').disabled=current===slides.length-1;history.replaceState(null,'',`#${current+1}`);overview.hidden=true}
function toggleNotes(){notes.hidden=!notes.hidden;document.getElementById('notesButton').setAttribute('aria-expanded',String(!notes.hidden))}async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch{}}
document.getElementById('prev').onclick=()=>show(current-1);document.getElementById('next').onclick=()=>show(current+1);document.getElementById('notesButton').onclick=toggleNotes;document.getElementById('fullscreen').onclick=fullscreen;document.getElementById('overviewButton').onclick=()=>overview.hidden=false;document.getElementById('closeOverview').onclick=()=>overview.hidden=true;
data.forEach((s,i)=>{const b=document.createElement('button');const n=document.createElement('span');n.textContent=`DIAPOSITIVA ${i+1}`;b.append(n,document.createTextNode(s.title.replaceAll('\n',' ')));b.onclick=()=>show(i);document.getElementById('overviewGrid').append(b)});
document.addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey||['INPUT','TEXTAREA'].includes(e.target.tagName))return;const k=e.key.toLowerCase();if(['arrowright','arrowdown',' ','pagedown'].includes(k)&&overview.hidden){e.preventDefault();show(current+1)}else if(['arrowleft','arrowup','pageup'].includes(k)&&overview.hidden){e.preventDefault();show(current-1)}else if(k==='home')show(0);else if(k==='end')show(slides.length-1);else if(k==='n')toggleNotes();else if(k==='f')fullscreen();else if(k==='o')overview.hidden=!overview.hidden;else if(k==='escape'){notes.hidden=true;overview.hidden=true;document.getElementById('notesButton').setAttribute('aria-expanded','false')}});
setInterval(()=>{const s=Math.floor((Date.now()-start)/1000);document.getElementById('timer').textContent=`${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`},1000);document.addEventListener('fullscreenchange',()=>document.body.classList.toggle('presenting',!!document.fullscreenElement));show(Number(location.hash.slice(1)||1)-1);
</script></body></html>'''
    template = template.replace('</style></head>', '.kind-queries pre{font-size:16px;line-height:1.5;padding:24px 20px}.kind-queries pre span{margin-bottom:14px}.kind-queries .query-layout{grid-template-columns:32% 1fr}.kind-queries h2{font-size:43px}</style></head>')
    template = re.sub(r'\.(cover|flow|table|queries|status|closing)(?![-\w])', r'.kind-\1', template)
    result = template.replace('__SLIDES__', '\n'.join(pages)).replace('__DATA__', json.dumps(SLIDES, ensure_ascii=False).replace('</', '<\\/'))
    (OUT/'Neifit_presentacion_animada.html').write_text(result, encoding='utf-8')


def make_pptx():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    def rect(slide,x,y,w,h,fill=WHITE,line=None,rounded=True):
        shape=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(fill)
        if line: shape.line.color.rgb=RGBColor.from_string(line)
        else: shape.line.fill.background()
        return shape
    def text(slide,x,y,w,h,value,size=20,color=BROWN,bold=False,font='Aptos',spacing=7):
        box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        tf=box.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=0;tf.margin_top=tf.margin_bottom=0
        for i,line in enumerate(value.split('\n')):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line
            p.font.size=Pt(size);p.font.name=font;p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color)
            p.space_after=Pt(spacing)
        return box
    def card(slide,x,y,w,h,title,body,index=None,size=18):
        rect(slide,x,y,w,h)
        top=y+.22
        if index is not None:
            text(slide,x+.22,top,w-.44,.48,f'{index:02}',27,GREEN,font='Georgia');top+=.6
        text(slide,x+.22,top,w-.44,.7,title,22,bold=True)
        text(slide,x+.22,top+.78,w-.44,h-(top-y)-.9,body,size,color='705540')
    def diagram(slide):
        nodes=[('Categorías',.7,2.05),('Productos',4.75,2.05),('Detalles de pedido',8.8,2.05),('Usuarios',.7,3.7),('Pedidos',4.75,3.7),('Seguimiento',8.8,3.7),('Cotizaciones',.7,5.35),('Detalles de cotización',4.75,5.35),('Transacciones de pago',8.8,5.35)]
        edges=[(0,1),(1,2),(3,4),(4,5),(3,6),(6,7),(4,8),(4,2)]
        for a,b in edges:
            _,x,y=nodes[a];_,xx,yy=nodes[b]
            if y==yy: sx,sy,ex,ey=x+2.7,y+.4,xx,yy+.4
            else: sx,sy,ex,ey=x+1.35,y+.8,xx+1.35,yy
            connector=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(sx), Inches(sy), Inches(ex), Inches(ey));connector.line.color.rgb=RGBColor.from_string(GREEN);connector.line.width=Pt(1.6)
            text(slide,(sx+ex)/2+.04,(sy+ey)/2-.26,.7,.3,'1 : N',11,GREEN)
        for title,x,y in nodes:
            rect(slide,x,y,2.7,.8,line='D7C4B4');text(slide,x+.12,y+.24,2.46,.45,title,16,bold=True)
    for i,s in enumerate(SLIDES):
        sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=RGBColor.from_string(CREAM)
        rect(sl,0,0,13.333,.07,GREEN,rounded=False)
        text(sl,.65,.35,9,.3,s['tag'],10,GREEN,True)
        text(sl,10.6,.35,2.1,.3,'NEIFIT / PROYECTO WEB',9,GREEN)
        text(sl,.65,7.04,10,.2,'NEIFIT · PRESENTACIÓN DEL PROYECTO · 10 NOV 2026',9,color='856954')
        text(sl,11.9,7.04,.9,.2,f'{i+1:02} / {len(SLIDES):02}',9,color='856954')
        if s['kind']=='cover':
            text(sl,.7,1.6,7,1.5,'Neifit',86,font='Georgia')
            text(sl,.75,3.25,7,1.3,s['subtitle'],29)
            text(sl,.75,5.1,7,1.65,'Integrantes\nMaribel Marín Cortés\nNixon Garcia\nFlor Neifix González\n10 de noviembre de 2026',16,GREEN)
            rect(sl,8.7,2.1,3.85,2.85)
            sl.shapes.add_picture(str(LOGO),Inches(8.85),Inches(2.25),width=Inches(3.55))
        else:
            text(sl,.65,.95,12,1.2,s['title'],36 if s['kind']!='closing' else 40,font='Georgia')
            text(sl,.65,2.05 if s['kind']=='closing' else 1.84,12,.55,s['subtitle'],17,color='7A5B47')
            if s['kind']=='diagram':diagram(sl)
            elif s['kind']=='table':
                rows=[s['headers']]+s['rows'];rh=.61 if len(rows)>5 else .73
                table=sl.shapes.add_table(len(rows),3,Inches(.65),Inches(2.45),Inches(12.03),Inches(rh*len(rows))).table
                for col,w in zip(table.columns,[2.8,5.15,4.08]):col.width=Inches(w)
                for ri,row in enumerate(rows):
                    for ci,value in enumerate(row):
                        cell=table.cell(ri,ci);cell.text=value;cell.fill.solid();cell.fill.fore_color.rgb=RGBColor.from_string(GREEN if ri==0 else WHITE)
                        cell.margin_left=Inches(.12);cell.margin_top=Inches(.11)
                        for p in cell.text_frame.paragraphs:
                            p.font.name='Aptos';p.font.size=Pt(14 if ri else 16);p.font.bold=ri==0 or ci==0;p.font.color.rgb=RGBColor.from_string('FFFFFF' if ri==0 else BROWN)
            elif s['kind']=='queries':
                for j,(title,body) in enumerate(s['cards']):
                    rect(sl,.65,2.65+j*1.05,4.0,.92);text(sl,.85,2.77+j*1.05,3.6,.3,title,18,bold=True);text(sl,.85,3.12+j*1.05,3.6,.34,body,13)
                rect(sl,4.95,2.65,7.72,3.5,fill='30251E')
                text(sl,5.2,2.85,7.2,.3,'SQL / POSTGRESQL',11,color='AAC596',bold=True)
                text(sl,5.2,3.28,7.2,2.75,s['sql'],12,color=CREAM,font='Consolas',spacing=0)
            else:
                cards=s.get('cards',[]);n=len(cards)
                if n==4 and s['kind']!='flow':
                    for j,(title,body) in enumerate(cards):card(sl,.65+(j%2)*6.1,2.65+(j//2)*1.65,5.9,1.48,title,body,None,16)
                else:
                    gap=.2;w=(12.03-(n-1)*gap)/n
                    for j,(title,body) in enumerate(cards):card(sl,.65+j*(w+gap),2.8,w,3.12,title,body,None if s['kind']=='closing' else j+1,18 if n<4 else 16)
            if s.get('takeaway'):
                rect(sl,.65,6.33,12.03,.46,fill='E4E7D6');text(sl,.8,6.41,11.75,.32,s['takeaway'],13,bold=True)
        sl.notes_slide.notes_text_frame.text=s['note']
        transition=OxmlElement('p:transition');transition.set('spd','med');transition.set('advClick','1');transition.append(OxmlElement('p:fade'));sl._element.append(transition)
    prs.save(OUT/'Neifit_presentacion_consultas.pptx')


def make_guide():
    guide='''# Neifit · Lista para presentar

Fecha: 10 de noviembre de 2026. Duración sugerida: 12–15 minutos (incluye cinco consultas SQL).

## Presentación animada

Abre Neifit_presentacion_animada.html con doble clic en Chrome o Edge. Funciona sin conexión, sin iniciar el proyecto y sin instalar nada.

- Flechas o espacio: avanzar y retroceder.
- F: pantalla completa.
- N: mostrar u ocultar el guion. Se ve en la misma pantalla: ocúltalo antes de proyectar si no quieres que el público lo vea.
- O: índice para saltar a una diapositiva.
- Inicio / Fin: primera o última diapositiva.
- Esc: cerrar guion o índice. El navegador también usa Esc para salir de pantalla completa.
- Ctrl + P: imprimir o guardar en PDF. Las animaciones se convierten en páginas estáticas.

La presentación HTML incluye sus recursos. No necesitas conexión a Canva, Google Fonts ni ningún CDN.

## Editar o importar en Canva

Abre Neifit_presentacion_consultas.pptx con PowerPoint, o entra a Canva y utiliza su opción de importar/subir archivo para cargar el PPTX. Los textos, tablas y diagramas se construyeron como elementos editables. Revisa tipografía y distribución después de importar. Las transiciones de PowerPoint pueden no conservarse en Canva: aplica allí las animaciones que prefieras. La versión HTML ya incluye animaciones.

No se creó ni publicó una presentación dentro de una cuenta de Canva. Este paquete contiene los archivos para usar o importar.

## Respaldo

Neifit_presentacion_consultas.pdf es la versión fija para exponer si no puedes utilizar el HTML o PowerPoint. El PDF no tiene animaciones.

## Antes de exponer

1. Abre el HTML y prueba las flechas, pantalla completa y guion.
2. Conserva el PDF y el PPTX como respaldo.
3. Si harás una demostración del sistema, inicia backend y frontend por separado. El HTML de la presentación no los necesita.
4. No proyectes .env, claves ni enlaces con tokens.
5. Explica que pedidos y cotizaciones siguen en memoria; no prometas persistencia ni pagos terminados.

## Guion por diapositiva

'''
    for i,s in enumerate(SLIDES):guide+=f'### {i+1}. {s["title"].replace(chr(10)," ")}\n\n{s["note"]}\n\n'
    (OUT/'GUIA_PARA_EXPONER.md').write_text(guide,encoding='utf-8')
    sql='''-- Ejemplos para el esquema diseñado. Consultas de solo lectura.
-- Requieren las tablas instaladas y registros persistidos.

-- Productos con pocas unidades.
select name, stock from public.products
where is_active = true and stock <= 5 order by stock;

-- Cotizaciones pendientes e importe de referencia.
select q.quote_number, q.customer_name, q.created_at,
  coalesce(sum(i.quantity * i.reference_price), 0) as total_referencia
from public.quotes q
left join public.quote_items i on i.quote_id = q.id
where q.status = 'pendiente'
group by q.id, q.quote_number, q.customer_name, q.created_at
order by q.created_at;

-- Pedidos pendientes de entrega, con o sin mensajero asignado.
select o.order_number, o.order_status,
  coalesce(p.full_name, 'Sin asignar') as mensajero
from public.orders o
left join public.profiles p on p.id = o.assigned_delivery_user_id
where o.order_status not in ('entregado','cancelado')
order by o.created_at;

-- Productos con más unidades en pedidos no cancelados y pago aprobado.
select p.name, sum(i.quantity) as unidades
from public.order_items i
join public.orders o on o.id = i.order_id
join public.products p on p.id = i.product_id
where o.payment_status = 'aprobado' and o.order_status <> 'cancelado'
group by p.id, p.name order by unidades desc;
'''
    sql = '-- PostgreSQL: cinco consultas de solo lectura para la exposición.\n-- Requieren tablas instaladas, datos persistidos y autorización.\n\n'
    sql += '\n\n'.join(f'-- {title}\n{query}' for title, _, _, _, query in CONSULTAS) + '\n'
    (OUT/'consultas_ejemplo.sql').write_text(sql,encoding='utf-8')


if __name__=='__main__':
    make_html();make_pptx();make_guide()
    print(f'Generadas {len(SLIDES)} diapositivas: HTML animado, PPTX editable y guía de exposición.')

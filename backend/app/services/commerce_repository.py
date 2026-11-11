"""Contratos entre tablas de Supabase y las respuestas que consume React."""
import re
import unicodedata
from uuid import uuid4
from fastapi import HTTPException
from app.core.supabase_rest import supabase_rest as db, uuid_value
from app.core.permissions import can_read_order, project_order
from app.core.tenant import current_company_id


def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def normalize_product(row):
    category = row.pop('categories', None) or {}
    row['sales_enabled'] = row.get('is_available', False)
    row['category_name'] = row.get('category_name') or category.get('name')
    row['category_slug'] = row.get('category_slug') or category.get('slug')
    row['is_available'] = bool(row.get('is_active', True) and row.get('is_available') and row.get('stock', 0) > 0 and category.get('is_active', True))
    return row


def _rename(row, mapping):
    if not isinstance(row, dict):
        return row
    return {mapping.get(key, key): value for key, value in row.items()}


ORDER_FIELDS = {
    'usuario_id': 'user_id', 'numero_pedido': 'order_number', 'nombre_cliente': 'customer_name',
    'telefono_cliente': 'customer_phone', 'correo_cliente': 'customer_email', 'direccion': 'address',
    'estado_pedido': 'order_status', 'estado_pago': 'payment_status', 'metodo_pago': 'payment_method',
    'costo_envio': 'shipping_cost', 'notas': 'notes',
    'usuario_mensajero_asignado_id': 'assigned_delivery_user_id', 'creado_en': 'created_at',
    'actualizado_en': 'updated_at', 'solicitud_id': 'request_id',
    'existencias_descontadas': 'stock_debited',
}
ITEM_FIELDS = {
    'pedido_id': 'order_id', 'cotizacion_id': 'quote_id', 'producto_id': 'product_id',
    'nombre_producto': 'product_name', 'cantidad': 'quantity',
    'precio_unitario': 'unit_price', 'precio_referencia': 'reference_price',
}
QUOTE_FIELDS = {
    'usuario_id': 'user_id', 'numero_cotizacion': 'quote_number', 'estado': 'status',
    'nombre_cliente': 'customer_name', 'telefono_cliente': 'customer_phone',
    'correo_cliente': 'customer_email', 'notas': 'notes', 'creado_en': 'created_at',
    'actualizado_en': 'updated_at', 'total_ofrecido': 'offered_total',
    'condiciones_oferta': 'offer_conditions', 'oferta_valida_hasta': 'offer_valid_until',
    'respondida_en': 'responded_at', 'respondida_por': 'responded_by',
}


def normalize_order(row):
    result = _rename(row, ORDER_FIELDS)
    result['items'] = [_rename(item, ITEM_FIELDS) for item in result.get('items', [])]
    result['tracking_history'] = [
        {'status': event.get('estado', event.get('status')),
         'message': event.get('mensaje', event.get('message')),
         'timestamp': event.get('timestamp', event.get('creado_en'))}
        for event in result.get('tracking_history', [])
    ]
    return result


def normalize_quote(row):
    result = _rename(row, QUOTE_FIELDS)
    result['items'] = [_rename(item, ITEM_FIELDS) for item in result.get('items', [])]
    return result


PRODUCT_INPUT_FIELDS = {
    'category_id': 'categoria_id', 'name': 'nombre', 'slug': 'identificador_url',
    'description': 'descripcion', 'ingredients': 'ingredientes', 'allergens': 'alergenos',
    'price': 'precio', 'stock': 'existencias', 'is_active': 'activo',
    'is_available': 'disponible', 'image_url': 'url_imagen', 'featured': 'destacado',
    'expected_updated_at': 'expected_updated_at',
}
PRODUCT_OUTPUT_FIELDS = {value: key for key, value in PRODUCT_INPUT_FIELDS.items()}
PRODUCT_OUTPUT_FIELDS.update({'creado_en': 'created_at', 'actualizado_en': 'updated_at'})
DOCUMENT_FIELDS = {
    'items': 'items', 'product_id': 'producto_id', 'product_name': 'nombre_producto',
    'quantity': 'cantidad', 'unit_price': 'precio_unitario', 'reference_price': 'precio_referencia',
    'customer_name': 'nombre_cliente', 'customer_phone': 'telefono_cliente',
    'customer_email': 'correo_cliente', 'address': 'direccion', 'notes': 'notas',
    'payment_method': 'metodo_pago',
}


class CommerceRepository:
    async def products(self, category=None, search=None, featured=None, available=None, include_inactive=False):
        params = {'select': 'id,category_id:categoria_id,name:nombre,slug:identificador_url,description:descripcion,ingredients:ingredientes,allergens:alergenos,price:precio,stock:existencias,is_active:activo,is_available:disponible,image_url:url_imagen,featured:destacado,created_at:creado_en,updated_at:actualizado_en,categories:categorias!inner(name:nombre,slug:identificador_url,is_active:activo)', 'order': 'creado_en.desc,id'}
        params['empresa_id'] = 'eq.' + current_company_id()
        if not include_inactive:
            params.update(activo='eq.true', **{'categorias.activo': 'eq.true'})
        if featured is not None:
            params['destacado'] = 'eq.' + str(featured).lower()
        rows = [normalize_product(row) for row in await db.rows('productos', params)]
        if category:
            rows = [row for row in rows if category in (row['category_id'], row['category_slug'])]
        if search:
            rows = [row for row in rows if search.casefold() in ((row['name'] or '') + ' ' + (row['description'] or '')).casefold()]
        if available is not None:
            rows = [row for row in rows if row['is_available'] == available]
        return rows

    async def product(self, slug, include_inactive=False):
        # Un solo filtro parametrizado; no interpolar búsquedas dentro de expresiones OR.
        from uuid import UUID
        try:
            key, value = 'id', str(UUID(slug))
        except ValueError:
            key, value = 'identificador_url', slug
        params = {'select': 'id,category_id:categoria_id,name:nombre,slug:identificador_url,description:descripcion,ingredients:ingredientes,allergens:alergenos,price:precio,stock:existencias,is_active:activo,is_available:disponible,image_url:url_imagen,featured:destacado,created_at:creado_en,updated_at:actualizado_en,categories:categorias!inner(name:nombre,slug:identificador_url,is_active:activo)', key: 'eq.' + value}
        params['empresa_id'] = 'eq.' + current_company_id()
        if not include_inactive:
            params.update(activo='eq.true', **{'categorias.activo': 'eq.true'})
        rows = await db.rows('productos', params)
        return normalize_product(rows[0]) if rows else None

    async def save_product(self, data, user, product_id=None):
        payload = data.model_dump(exclude_unset=True, exclude={'category_name', 'category_slug'}, mode='json')
        if 'category_id' in payload:
            payload['category_id'] = uuid_value(payload['category_id'], 'Categoría')
        if not product_id:
            payload = {**data.model_dump(exclude={'category_name', 'category_slug'}, exclude_none=True, mode='json'), **payload}
            payload['slug'] = payload.get('slug') or slugify(payload['name'])
            if not payload['slug']:
                raise HTTPException(status_code=422,detail='Escribe un slug con letras o números')
            payload.setdefault('is_available', True)
        if payload.get('description') is None:
            payload.pop('description', None)
        translated = {PRODUCT_INPUT_FIELDS.get(key, key): value for key, value in payload.items()}
        result = await db.rpc('neifit_guardar_producto', p_actor=user['id'], p_datos=translated,
                              p_id=uuid_value(product_id) if product_id else None,
                              p_empresa=current_company_id())
        return normalize_product(_rename(result, PRODUCT_OUTPUT_FIELDS))

    async def deactivate_product(self, product_id, user):
        await db.rpc('neifit_guardar_producto', p_actor=user['id'], p_id=uuid_value(product_id),
                     p_datos={'activo': False, 'disponible': False}, p_empresa=current_company_id())
        return True

    async def categories(self):
        return await db.rows('categorias', {'select': 'id,name:nombre,slug:identificador_url,description:descripcion,image:url_imagen,is_active:activo', 'empresa_id': 'eq.' + current_company_id(), 'activo': 'eq.true', 'order': 'nombre'})

    async def create_category(self, data):
        payload = data.model_dump(exclude_none=True)
        payload['slug'] = payload.get('slug') or slugify(payload['name'])
        if not payload['slug']:
            raise HTTPException(status_code=422,detail='Escribe un slug con letras o números')
        translated = {'empresa_id': current_company_id(), 'nombre': payload['name'], 'identificador_url': payload['slug'],
                      'descripcion': payload.get('description') or '', 'url_imagen': payload.get('image'),
                      'activo': payload.get('is_active', True)}
        rows = await db.request('POST', 'categorias', data=translated, headers={'Prefer': 'return=representation'})
        return _rename(rows[0], {'nombre': 'name', 'identificador_url': 'slug', 'descripcion': 'description',
                                 'url_imagen': 'image', 'activo': 'is_active'})

    async def create_document(self, kind, data, user):
        payload = data.model_dump(exclude={'user_id', 'request_id'}, mode='json')
        for item in payload['items']:
            item['product_id'] = uuid_value(item['product_id'], 'Producto')
        translated = {DOCUMENT_FIELDS.get(key, key): value for key, value in payload.items()}
        translated['items'] = [{DOCUMENT_FIELDS.get(key, key): value for key, value in item.items()}
                               for item in payload['items']]
        result = await db.rpc('neifit_crear_documento', p_actor=user['id'], p_tipo=kind,
                              p_solicitud=str(data.request_id or uuid4()), p_datos=translated,
                              p_empresa=current_company_id())
        return normalize_order(result) if kind == 'order' else normalize_quote(result)

    async def orders(self, user, order_id=None, tracking=None):
        rows = await db.rpc('neifit_leer_pedidos', p_actor=user['id'],
                            p_id=uuid_value(order_id) if order_id else None, p_seguimiento=tracking,
                            p_empresa=current_company_id())
        # También proyectar la respuesta: mensajería no recibe importes ni datos de pago.
        rows = [normalize_order(row) for row in rows]
        return [project_order(user, row) for row in rows if can_read_order(user, row)]

    async def update_order(self, order_id, data, user):
        row = await db.rpc('neifit_actualizar_pedido', p_actor=user['id'], p_id=uuid_value(order_id),
                           p_estado=data.status, p_mensaje=data.message or '', p_empresa=current_company_id())
        return project_order(user, normalize_order(row))

    async def assign_delivery(self, order_id, delivery_id, user):
        row = await db.rpc('neifit_asignar_mensajero', p_actor=user['id'], p_id=uuid_value(order_id),
                           p_mensajero=uuid_value(delivery_id) if delivery_id else None,
                           p_empresa=current_company_id())
        return normalize_order(row)

    async def delivery_users(self):
        # Solo se llama desde un endpoint protegido por orders.manage.
        members = await db.rows('miembros_empresa', {'select': 'id:usuario_id,role:rol,perfiles!inner(full_name:nombre_completo)', 'empresa_id': 'eq.' + current_company_id(), 'estado': 'eq.activo'})
        profiles = [{'id': row['id'], 'role': row['role'], 'full_name': row['perfiles']['full_name']} for row in members]
        from app.services.access_service import access_service
        permissions = {}
        for role in {row['role'] for row in profiles}:
            permissions[role] = await access_service.permissions_for_role(role)
        return [row for row in profiles if 'delivery.read_assigned' in permissions[row['role']]]

    async def quotes(self, user):
        return [normalize_quote(row) for row in await db.rpc('neifit_leer_cotizaciones', p_actor=user['id'], p_empresa=current_company_id())]

    async def update_quote(self, quote_id, status, user):
        row = await db.rpc('neifit_actualizar_cotizacion', p_actor=user['id'], p_id=uuid_value(quote_id), p_estado=status, p_empresa=current_company_id())
        return normalize_quote(row)


commerce = CommerceRepository()

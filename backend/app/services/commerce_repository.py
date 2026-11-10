"""Contratos entre tablas de Supabase y las respuestas que consume React."""
import re
import unicodedata
from uuid import uuid4
from fastapi import HTTPException
from app.core.supabase_rest import supabase_rest as db, uuid_value
from app.core.permissions import can_read_order, project_order


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


class CommerceRepository:
    async def products(self, category=None, search=None, featured=None, available=None, include_inactive=False):
        params = {'select': '*,categories!inner(name,slug,is_active)', 'order': 'created_at.desc,id'}
        if not include_inactive:
            params.update(is_active='eq.true', **{'categories.is_active': 'eq.true'})
        if featured is not None:
            params['featured'] = 'eq.' + str(featured).lower()
        rows = [normalize_product(row) for row in await db.rows('products', params)]
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
            key, value = 'slug', slug
        params = {'select': '*,categories!inner(name,slug,is_active)', key: 'eq.' + value}
        if not include_inactive:
            params.update(is_active='eq.true', **{'categories.is_active': 'eq.true'})
        rows = await db.rows('products', params)
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
        result = await db.rpc('neifit_save_product', p_actor=user['id'], p_data=payload,
                              p_id=uuid_value(product_id) if product_id else None)
        return result

    async def deactivate_product(self, product_id, user):
        await db.rpc('neifit_save_product', p_actor=user['id'], p_id=uuid_value(product_id),
                     p_data={'is_active': False, 'is_available': False})
        return True

    async def categories(self):
        return await db.rows('categories', {'select': '*', 'is_active': 'eq.true', 'order': 'name'})

    async def create_category(self, data):
        payload = data.model_dump(exclude_none=True)
        payload['slug'] = payload.get('slug') or slugify(payload['name'])
        if not payload['slug']:
            raise HTTPException(status_code=422,detail='Escribe un slug con letras o números')
        rows = await db.request('POST', 'categories', data=payload, headers={'Prefer': 'return=representation'})
        return rows[0]

    async def create_document(self, kind, data, user):
        payload = data.model_dump(exclude={'user_id', 'request_id'}, mode='json')
        for item in payload['items']:
            item['product_id'] = uuid_value(item['product_id'], 'Producto')
        return await db.rpc('neifit_create_document', p_actor=user['id'], p_kind=kind,
                            p_request=str(data.request_id or uuid4()), p_data=payload)

    async def orders(self, user, order_id=None, tracking=None):
        rows = await db.rpc('neifit_read_orders', p_actor=user['id'],
                            p_id=uuid_value(order_id) if order_id else None, p_tracking=tracking)
        # También proyectar la respuesta: mensajería no recibe importes ni datos de pago.
        return [project_order(user, row) for row in rows if can_read_order(user, row)]

    async def update_order(self, order_id, data, user):
        row = await db.rpc('neifit_update_order', p_actor=user['id'], p_id=uuid_value(order_id),
                           p_status=data.status, p_message=data.message or '')
        return project_order(user, row)

    async def assign_delivery(self, order_id, delivery_id, user):
        return await db.rpc('neifit_assign_delivery', p_actor=user['id'], p_id=uuid_value(order_id),
                            p_delivery=uuid_value(delivery_id) if delivery_id else None)

    async def delivery_users(self):
        # Solo se llama desde un endpoint protegido por orders.manage.
        profiles = await db.rows('profiles', {'select': 'id,full_name,role', 'order': 'full_name'})
        from app.services.access_service import access_service
        permissions = {}
        for role in {row['role'] for row in profiles}:
            permissions[role] = await access_service.permissions_for_role(role)
        return [row for row in profiles if 'delivery.read_assigned' in permissions[row['role']]]

    async def quotes(self, user):
        return await db.rpc('neifit_read_quotes', p_actor=user['id'])

    async def update_quote(self, quote_id, status, user):
        return await db.rpc('neifit_update_quote', p_actor=user['id'], p_id=uuid_value(quote_id), p_status=status)


commerce = CommerceRepository()

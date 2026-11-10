from urllib.parse import urlencode
from fastapi import HTTPException
from app.core.supabase_rest import supabase_rest as db, uuid_value


class SiteRepository:
    async def settings(self):
        rows = await db.rows('company_settings', {'select': '*', 'singleton': 'eq.true'})
        if not rows:
            raise HTTPException(status_code=503, detail='Falta la configuración de la empresa')
        result = rows[0]
        result['whatsapp_url'] = 'https://wa.me/' + (result.get('whatsapp_number') or '')
        result['map_search_url'] = result.get('map_url') or 'https://www.google.com/maps/search/?' + urlencode({
            'api': '1', 'query': ', '.join(filter(None, [result.get('address'), result.get('city')]))})
        hours = result.get('opening_hours') or {}
        if 'weekdays' not in hours:
            hours = {**hours, 'weekdays': 'Lunes a viernes: ' + (hours.get('monday') or 'No informado'),
                     'weekends': 'No informado' if not hours.get('saturday') and not hours.get('sunday') else 'Consultar horario'}
        result['opening_hours'] = hours
        return result

    async def update_settings(self, data):
        allowed = {'business_name','phone_public','whatsapp_number','address','city','opening_hours','map_url','logo_url','shipping_cost'}
        payload = {key: value for key, value in data.items() if key in allowed}
        if 'shipping_cost' in payload:
            from decimal import Decimal, InvalidOperation
            try:
                value = Decimal(str(payload['shipping_cost']))
                if not value.is_finite() or value < 0:
                    raise InvalidOperation()
            except InvalidOperation:
                raise HTTPException(status_code=422, detail='Costo de domicilio inválido') from None
        if payload:
            await db.request('PATCH','company_settings',params={'singleton':'eq.true'},data=payload)
        return await self.settings()

    async def content(self):
        rows = await db.rows('site_content', {'select':'key,body','is_published':'eq.true'})
        return {row['key']: row['body'] for row in rows}

    async def update_content(self, data, user):
        allowed = {'hero_title','hero_description','about_us','mission','vision'}
        rows = []
        for key, value in data.items():
            if key not in allowed or not isinstance(value,str) or not value.strip() or len(value)>10000:
                raise HTTPException(status_code=422,detail='Contenido institucional inválido')
            rows.append({'key':key,'body':value.strip(),'is_published':True,'updated_by':user['id']})
        if rows:
            await db.request('POST','site_content',params={'on_conflict':'key'},data=rows,headers={'Prefer':'resolution=merge-duplicates'})
        return await self.content()

    async def values(self):
        return await db.rows('company_values',{'select':'*','is_published':'eq.true','order':'sort_order,id'})

    async def update_values(self, data):
        current = await self.values()
        if len(data)!=len(current) or {row.get('id') for row in data}!={row['id'] for row in current}:
            raise HTTPException(status_code=422,detail='Actualiza los valores existentes sin eliminar ni duplicar registros')
        rows=[]
        for row in data:
            if not isinstance(row.get('title'),str) or not row['title'].strip():
                raise HTTPException(status_code=422,detail='Cada valor requiere un título')
            rows.append({'id':uuid_value(row['id']),'title':row['title'].strip(),'description':row.get('description',''),
                         'sort_order':row.get('sort_order',0),'is_published':True})
        await db.request('POST','company_values',params={'on_conflict':'id'},data=rows,headers={'Prefer':'resolution=merge-duplicates'})
        return await self.values()


site_repository=SiteRepository()

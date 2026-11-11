from urllib.parse import urlencode
from fastapi import HTTPException
from app.core.supabase_rest import supabase_rest as db, uuid_value
from app.core.tenant import current_company_id


class SiteRepository:
    async def theme(self):
        rows = await db.rows('temas_empresa', {
            'select': 'primary_color:color_primario,secondary_color:color_secundario,accent_color:color_acento,background_color:color_fondo,surface_color:color_superficie,text_color:color_texto,logo_url:url_logo,icon_url:url_icono,cover_url:url_portada,heading_font:tipografia_titulos,body_font:tipografia_texto,border_radius:radio_bordes,button_style:estilo_botones,published:publicado,updated_at:actualizado_en',
            'empresa_id': 'eq.' + current_company_id(), 'publicado': 'eq.true', 'limit': '1'})
        if not rows:
            raise HTTPException(status_code=503, detail='Falta configurar la apariencia de la empresa')
        return rows[0]

    async def update_theme(self, data, user):
        fields = {'primary_color':'color_primario','secondary_color':'color_secundario',
                  'accent_color':'color_acento','background_color':'color_fondo',
                  'surface_color':'color_superficie','text_color':'color_texto','logo_url':'url_logo',
                  'icon_url':'url_icono','cover_url':'url_portada','heading_font':'tipografia_titulos',
                  'body_font':'tipografia_texto','border_radius':'radio_bordes',
                  'button_style':'estilo_botones','published':'publicado'}
        payload = {fields[key]: value for key,value in data.model_dump().items()}
        result = await db.rpc('neifit_guardar_tema',p_actor=user['id'],p_empresa=current_company_id(),p_tema=payload)
        return {key: result.get(column) for key,column in fields.items()} | {'updated_at': result.get('actualizado_en')}

    async def settings(self):
        rows = await db.rows('configuracion_empresa', {
            'select': 'id,business_name:nombre_negocio,phone_public:telefono_publico,whatsapp_number:numero_whatsapp,address:direccion,city:ciudad,opening_hours:horario_atencion,map_url:url_mapa,logo_url:url_logo,shipping_cost:costo_envio,updated_at:actualizado_en',
            'empresa_id': 'eq.' + current_company_id()})
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
            fields = {'business_name':'nombre_negocio','phone_public':'telefono_publico',
                      'whatsapp_number':'numero_whatsapp','address':'direccion','city':'ciudad',
                      'opening_hours':'horario_atencion','map_url':'url_mapa','logo_url':'url_logo',
                      'shipping_cost':'costo_envio'}
            await db.request('PATCH','configuracion_empresa',params={'empresa_id':'eq.' + current_company_id()},
                             data={fields[key]: value for key, value in payload.items()})
        return await self.settings()

    async def content(self):
        rows = await db.rows('contenido_sitio', {'select':'key:clave,body:cuerpo','empresa_id':'eq.' + current_company_id(),'publicado':'eq.true'})
        return {row['key']: row['body'] for row in rows}

    async def update_content(self, data, user):
        allowed = {'hero_title','hero_description','about_us','mission','vision'}
        rows = []
        for key, value in data.items():
            if key not in allowed or not isinstance(value,str) or not value.strip() or len(value)>10000:
                raise HTTPException(status_code=422,detail='Contenido institucional inválido')
            rows.append({'empresa_id':current_company_id(),'clave':key,'cuerpo':value.strip(),'publicado':True,'actualizado_por':user['id']})
        if rows:
            await db.request('POST','contenido_sitio',params={'on_conflict':'empresa_id,clave'},data=rows,headers={'Prefer':'resolution=merge-duplicates'})
        return await self.content()

    async def values(self):
        return await db.rows('valores_empresa',{'select':'id,title:titulo,description:descripcion,sort_order:orden,is_published:publicado','empresa_id':'eq.' + current_company_id(),'publicado':'eq.true','order':'orden,id'})

    async def update_values(self, data):
        current = await self.values()
        if len(data)!=len(current) or {row.get('id') for row in data}!={row['id'] for row in current}:
            raise HTTPException(status_code=422,detail='Actualiza los valores existentes sin eliminar ni duplicar registros')
        rows=[]
        for row in data:
            if not isinstance(row.get('title'),str) or not row['title'].strip():
                raise HTTPException(status_code=422,detail='Cada valor requiere un título')
            rows.append({'id':uuid_value(row['id']),'empresa_id':current_company_id(),'titulo':row['title'].strip(),'descripcion':row.get('description',''),
                         'orden':row.get('sort_order',0),'publicado':True})
        await db.request('POST','valores_empresa',params={'on_conflict':'id'},data=rows,headers={'Prefer':'resolution=merge-duplicates'})
        return await self.values()


site_repository=SiteRepository()

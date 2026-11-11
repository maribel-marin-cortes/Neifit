"""Perfil propio; el propietario siempre procede del JWT validado."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import require_permission
from app.core.supabase_rest import supabase_rest as db
from app.core.tenant import current_company_id

router = APIRouter()
own_profile = require_permission('profile.read')


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    full_name: str = Field(min_length=3, max_length=100)
    phone: str = Field(min_length=7, max_length=30)


class AddressInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    label: str = Field(min_length=2, max_length=50)
    address: str = Field(min_length=5, max_length=300)
    city: str = Field(min_length=3, max_length=100)
    recipient: str = Field(min_length=3, max_length=100)
    phone: str = Field(min_length=7, max_length=30)
    notes: str = Field(default='', max_length=500)


@router.get('')
async def get_account(user=Depends(own_profile)):
    rows = await db.rows('perfiles', {'id': 'eq.' + user['id'], 'select': 'id,full_name:nombre_completo,email:correo,phone:telefono'})
    if not rows:
        raise HTTPException(404, 'Perfil no encontrado')
    addresses = await db.rows('direcciones_cliente', {'empresa_id': 'eq.' + current_company_id(), 'usuario_id': 'eq.' + user['id'], 'select': 'id,label:etiqueta,address:direccion,city:ciudad,recipient:destinatario,phone:telefono,notes:notas', 'order': 'creado_en,id'})
    return {**rows[0], 'addresses': addresses}


@router.patch('')
async def update_profile(data: ProfileUpdate, user=Depends(own_profile)):
    await db.request('PATCH', 'perfiles', params={'id': 'eq.' + user['id']}, data={'nombre_completo': data.full_name, 'telefono': data.phone})
    return await get_account(user)


@router.post('/direcciones', status_code=201)
@router.post('/addresses', status_code=201, deprecated=True)
async def create_address(data: AddressInput, user=Depends(own_profile)):
    payload = {'empresa_id': current_company_id(), 'usuario_id': user['id'], 'etiqueta': data.label, 'direccion': data.address,
               'ciudad': data.city, 'destinatario': data.recipient, 'telefono': data.phone, 'notas': data.notes}
    rows = await db.request('POST', 'direcciones_cliente', data=payload, headers={'Prefer': 'return=representation'})
    return _address_out(rows[0])


@router.put('/direcciones/{address_id}')
@router.put('/addresses/{address_id}', deprecated=True)
async def update_address(address_id: UUID, data: AddressInput, user=Depends(own_profile)):
    payload = {'etiqueta': data.label, 'direccion': data.address, 'ciudad': data.city,
               'destinatario': data.recipient, 'telefono': data.phone, 'notas': data.notes}
    rows = await db.request('PATCH', 'direcciones_cliente', params={'id': 'eq.' + str(address_id), 'empresa_id': 'eq.' + current_company_id(), 'usuario_id': 'eq.' + user['id']}, data=payload, headers={'Prefer': 'return=representation'})
    if not rows:
        raise HTTPException(404, 'Dirección no encontrada')
    return _address_out(rows[0])


@router.delete('/direcciones/{address_id}')
@router.delete('/addresses/{address_id}', deprecated=True)
async def delete_address(address_id: UUID, user=Depends(own_profile)):
    rows = await db.request('DELETE', 'direcciones_cliente', params={'id': 'eq.' + str(address_id), 'empresa_id': 'eq.' + current_company_id(), 'usuario_id': 'eq.' + user['id']}, headers={'Prefer': 'return=representation'})
    if not rows:
        raise HTTPException(404, 'Dirección no encontrada')
    return {'deleted': True}


def _address_out(row):
    return {
        'id': row['id'], 'label': row.get('etiqueta', row.get('label')),
        'address': row.get('direccion', row.get('address')),
        'city': row.get('ciudad', row.get('city')),
        'recipient': row.get('destinatario', row.get('recipient')),
        'phone': row.get('telefono', row.get('phone')),
        'notes': row.get('notas', row.get('notes', '')),
    }

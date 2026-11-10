"""Perfil propio; el propietario siempre procede del JWT validado."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import require_permission
from app.core.supabase_rest import supabase_rest as db

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
    rows = await db.rows('profiles', {'id': 'eq.' + user['id'], 'select': 'id,full_name,email,phone'})
    if not rows:
        raise HTTPException(404, 'Perfil no encontrado')
    addresses = await db.rows('customer_addresses', {'user_id': 'eq.' + user['id'], 'select': 'id,label,address,city,recipient,phone,notes', 'order': 'created_at,id'})
    return {**rows[0], 'addresses': addresses}


@router.patch('')
async def update_profile(data: ProfileUpdate, user=Depends(own_profile)):
    await db.request('PATCH', 'profiles', params={'id': 'eq.' + user['id']}, data=data.model_dump())
    return await get_account(user)


@router.post('/addresses', status_code=201)
async def create_address(data: AddressInput, user=Depends(own_profile)):
    rows = await db.request('POST', 'customer_addresses', data={**data.model_dump(), 'user_id': user['id']}, headers={'Prefer': 'return=representation'})
    return rows[0]


@router.put('/addresses/{address_id}')
async def update_address(address_id: UUID, data: AddressInput, user=Depends(own_profile)):
    rows = await db.request('PATCH', 'customer_addresses', params={'id': 'eq.' + str(address_id), 'user_id': 'eq.' + user['id']}, data=data.model_dump(), headers={'Prefer': 'return=representation'})
    if not rows:
        raise HTTPException(404, 'Dirección no encontrada')
    return rows[0]


@router.delete('/addresses/{address_id}')
async def delete_address(address_id: UUID, user=Depends(own_profile)):
    rows = await db.request('DELETE', 'customer_addresses', params={'id': 'eq.' + str(address_id), 'user_id': 'eq.' + user['id']}, headers={'Prefer': 'return=representation'})
    if not rows:
        raise HTTPException(404, 'Dirección no encontrada')
    return {'deleted': True}

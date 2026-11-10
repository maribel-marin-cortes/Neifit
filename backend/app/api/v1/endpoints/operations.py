from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import require_auth, require_admin, require_permission
from app.core.supabase_rest import supabase_rest as db

router = APIRouter()


class QuoteResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    total: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    conditions: str = Field(min_length=10, max_length=3000)
    valid_until: datetime


class CashReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reference: str = Field(min_length=3, max_length=200)
    confirmed_received: bool


@router.get('/notifications')
async def notifications(user=Depends(require_auth)):
    return await db.request('GET', 'notifications', params={'user_id': 'eq.' + user['id'], 'select': 'id,title,message,link,created_at,read_at', 'order': 'created_at.desc,id', 'limit': '50'})


@router.patch('/notifications/{notice_id}/read')
async def mark_read(notice_id: UUID, user=Depends(require_auth)):
    await db.request('PATCH', 'notifications', params={'id': 'eq.' + str(notice_id), 'user_id': 'eq.' + user['id'], 'read_at': 'is.null'}, data={'read_at': datetime.now(timezone.utc).isoformat()})
    return {'ok': True}


@router.post('/quotes/{quote_id}/response')
async def respond_quote(quote_id: UUID, data: QuoteResponse, user=Depends(require_permission('quotes.manage'))):
    return await db.rpc('neifit_respond_quote', p_actor=user['id'], p_id=str(quote_id), p_total=str(data.total), p_conditions=data.conditions, p_valid_until=data.valid_until.isoformat())


@router.post('/orders/{order_id}/cash-receipt')
async def confirm_cash(order_id: UUID, data: CashReceipt, user=Depends(require_admin)):
    if not data.confirmed_received:
        raise HTTPException(422, 'Confirma que recibiste efectivamente el dinero')
    return await db.rpc('neifit_confirm_cash', p_actor=user['id'], p_id=str(order_id), p_amount=str(data.amount), p_reference=data.reference)

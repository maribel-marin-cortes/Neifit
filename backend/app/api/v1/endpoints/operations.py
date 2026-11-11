from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import require_auth, require_admin, require_permission
from app.core.supabase_rest import supabase_rest as db
from app.services.commerce_repository import normalize_order, normalize_quote
from app.core.tenant import current_company_id

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


@router.get('/notificaciones')
@router.get('/notifications', deprecated=True)
async def notifications(user=Depends(require_auth)):
    return await db.request('GET', 'notificaciones', params={'empresa_id': 'eq.' + current_company_id(), 'usuario_id': 'eq.' + user['id'], 'select': 'id,title:titulo,message:mensaje,link:enlace,created_at:creado_en,read_at:leido_en', 'order': 'creado_en.desc,id', 'limit': '50'})


@router.patch('/notificaciones/{notice_id}/leer')
@router.patch('/notifications/{notice_id}/read', deprecated=True)
async def mark_read(notice_id: UUID, user=Depends(require_auth)):
    await db.request('PATCH', 'notificaciones', params={'id': 'eq.' + str(notice_id), 'empresa_id': 'eq.' + current_company_id(), 'usuario_id': 'eq.' + user['id'], 'leido_en': 'is.null'}, data={'leido_en': datetime.now(timezone.utc).isoformat()})
    return {'ok': True}


@router.post('/cotizaciones/{quote_id}/respuesta')
@router.post('/quotes/{quote_id}/response', deprecated=True)
async def respond_quote(quote_id: UUID, data: QuoteResponse, user=Depends(require_permission('quotes.manage'))):
    result = await db.rpc('neifit_responder_cotizacion', p_actor=user['id'], p_id=str(quote_id),
                          p_total=str(data.total), p_condiciones=data.conditions,
                          p_valida_hasta=data.valid_until.isoformat(), p_empresa=current_company_id())
    return normalize_quote(result)


@router.post('/pedidos/{order_id}/recibo-efectivo')
@router.post('/orders/{order_id}/cash-receipt', deprecated=True)
async def confirm_cash(order_id: UUID, data: CashReceipt, user=Depends(require_admin)):
    if not data.confirmed_received:
        raise HTTPException(422, 'Confirma que recibiste efectivamente el dinero')
    result = await db.rpc('neifit_confirmar_efectivo', p_actor=user['id'], p_id=str(order_id),
                          p_importe=str(data.amount), p_referencia=data.reference,
                          p_empresa=current_company_id())
    return normalize_order(result)

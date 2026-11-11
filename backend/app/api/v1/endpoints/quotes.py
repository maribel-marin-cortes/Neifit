from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.quote import QuoteOut, QuoteCreate, QuoteStatusUpdate
from app.services.commerce_repository import commerce
from uuid import UUID
from app.core.security import require_auth, require_admin, require_permission
from app.services.quote_service import QuoteService

router = APIRouter()
service = QuoteService()


@router.get("/", response_model=List[QuoteOut])
async def list_quotes(user=Depends(require_permission('quotes.read_own', 'quotes.manage'))):
    """Lista de cotizaciones. Admin ve todas; cliente solo las suyas."""
    return await service.list_for_user(user)


@router.post("/", response_model=QuoteOut, status_code=201)
async def create_quote(data: QuoteCreate, user=Depends(require_permission('quotes.create'))):
    """Crear cotización de un cliente autenticado."""
    return await service.create(data, user)


@router.patch('/{quote_id}/estado', response_model=QuoteOut)
@router.patch('/{quote_id}/status', response_model=QuoteOut, deprecated=True)
async def update_quote(quote_id: UUID, data: QuoteStatusUpdate, user=Depends(require_permission('quotes.manage'))):
    return await commerce.update_quote(str(quote_id), data.status, user)


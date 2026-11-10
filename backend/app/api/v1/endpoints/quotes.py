from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.quote import QuoteOut, QuoteCreate
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
    """Crear cotización (público, sin autenticación requerida)."""
    return await service.create(data, user)


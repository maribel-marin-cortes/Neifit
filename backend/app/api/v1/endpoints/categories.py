from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.category import CategoryOut, CategoryCreate
from app.core.security import require_admin, require_auth, require_permission
from app.services.category_service import CategoryService

router = APIRouter()
service = CategoryService()


@router.get("/", response_model=List[CategoryOut])
async def list_categories(user=Depends(require_permission('catalog.read', 'products.manage', 'quotes.create'))):
    """Lista pública de categorías activas."""
    return await service.list_active()


@router.post("/", response_model=CategoryOut, status_code=201)
async def create_category(data: CategoryCreate, admin=Depends(require_permission('products.manage'))):
    """Crear categoría. Solo administradores."""
    return await service.create(data)


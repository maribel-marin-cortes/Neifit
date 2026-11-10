from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.product import ProductOut, ProductCreate, ProductUpdate
from app.core.security import require_admin, require_auth, require_permission
from app.services.product_service import ProductService
from app.core.permissions import has_permission

router = APIRouter()
service = ProductService()


@router.get("/", response_model=List[ProductOut])
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    available: Optional[bool] = None,
    include_inactive: bool = False,
    user=Depends(require_permission('catalog.read', 'products.manage', 'quotes.create')),
):
    """Catálogo completo para usuarios autenticados."""
    return await service.list_products(
        category=category, search=search,
        featured=featured, available=available,
        include_inactive=include_inactive and has_permission(user,'products.manage')
    )


@router.get("/{slug}", response_model=ProductOut)
async def get_product(slug: str, user=Depends(require_permission('catalog.read', 'products.manage'))):
    """Detalle de producto por slug o id."""
    product = await service.get_by_slug(slug, include_inactive=has_permission(user,'products.manage'))
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/", response_model=ProductOut, status_code=201)
async def create_product(
    data: ProductCreate,
    admin=Depends(require_permission('products.manage'))
):
    """Crear producto. Solo administradores."""
    return await service.create(data, admin)


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    admin=Depends(require_permission('products.manage'))
):
    """Actualizar producto. Solo administradores."""
    updated = await service.update(product_id, data, admin)
    if not updated:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return updated


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    admin=Depends(require_permission('products.manage'))
):
    """Eliminar producto. Solo administradores."""
    deleted = await service.delete(product_id, admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="Producto no encontrado")


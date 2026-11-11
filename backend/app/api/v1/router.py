from fastapi import APIRouter, Depends
from app.core.security import require_auth
from app.core.tenant import establish_company
from app.api.v1.endpoints import products, categories, orders, quotes, tracking, site
from app.api.v1.endpoints import access
from app.api.v1.endpoints import account
from app.api.v1.endpoints import operations
from app.api.v1.endpoints import companies

api_router = APIRouter(dependencies=[Depends(establish_company)])
api_router.include_router(operations.router, tags=['Operación'])
api_router.include_router(account.router, prefix='/cuenta', tags=['Mi cuenta'])
api_router.include_router(account.router, prefix='/account', tags=['Compatibilidad'], deprecated=True)


@api_router.get('/autenticacion/yo', tags=['Autenticación'])
@api_router.get('/auth/me', tags=['Compatibilidad'], deprecated=True)
async def current_profile(user: dict = Depends(require_auth)):
    """Verifica el JWT y devuelve el perfil autorizado de la sesión."""
    return user

api_router.include_router(categories.router, prefix="/categorias", tags=["Categorías"])
api_router.include_router(products.router, prefix="/productos", tags=["Productos"])
api_router.include_router(orders.router, prefix="/pedidos", tags=["Pedidos"])
api_router.include_router(quotes.router, prefix="/cotizaciones", tags=["Cotizaciones"])
api_router.include_router(tracking.router, prefix="/seguimiento", tags=["Trazabilidad"])
api_router.include_router(site.router, prefix="/sitio", tags=["Contenido del sitio"])
api_router.include_router(access.router, prefix='/accesos', tags=['Roles y permisos'])
api_router.include_router(companies.router, prefix='/empresas', tags=['Empresas'])

# Alias temporales: se retiran cuando todos los clientes usen las rutas en español.
api_router.include_router(categories.router, prefix="/categories", tags=["Compatibilidad"], deprecated=True)
api_router.include_router(products.router, prefix="/products", tags=["Compatibilidad"], deprecated=True)
api_router.include_router(orders.router, prefix="/orders", tags=["Compatibilidad"], deprecated=True)
api_router.include_router(quotes.router, prefix="/quotes", tags=["Compatibilidad"], deprecated=True)
api_router.include_router(tracking.router, prefix="/tracking", tags=["Compatibilidad"], deprecated=True)
api_router.include_router(site.router, prefix="/site", tags=["Compatibilidad"], deprecated=True)
api_router.include_router(access.router, prefix='/access', tags=['Compatibilidad'], deprecated=True)


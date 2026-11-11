from fastapi import APIRouter, Depends
from app.core.security import require_admin, require_permission
from app.schemas.product import ProductPreview
from app.schemas.category import CategoryOut
from app.services.product_service import ProductService
from app.services.category_service import CategoryService
from app.core.supabase_rest import database_enabled
from app.services.site_repository import site_repository
from app.schemas.theme import CompanyTheme

router = APIRouter()

DEFAULT_THEME = CompanyTheme().model_dump()


@router.get('/tema')
@router.get('/theme', deprecated=True)
async def get_theme():
    return await site_repository.theme() if database_enabled() else DEFAULT_THEME


@router.put('/tema')
@router.put('/theme', deprecated=True)
async def update_theme(data: CompanyTheme, admin=Depends(require_permission('appearance.manage'))):
    return await site_repository.update_theme(data, admin) if database_enabled() else data.model_dump()


@router.get('/productos-destacados', response_model=list[ProductPreview])
@router.get('/featured-products', response_model=list[ProductPreview], deprecated=True)
async def featured_products():
    """Solo la muestra de portada, sin cantidades de inventario ni datos privados."""
    return (await ProductService().list_products(featured=True))[:3]


@router.get('/categorias', response_model=list[CategoryOut])
@router.get('/categories', response_model=list[CategoryOut], deprecated=True)
async def landing_categories():
    return await CategoryService().list_active()

# Datos confirmados del negocio (fuente de verdad inicial)
_SETTINGS = {
    "business_name": "Neifit",
    "phone_public": "+57 3127827020",
    "whatsapp_number": "573127827020",
    "whatsapp_url": "https://wa.me/573127827020",
    "address": "CR 28B # 38F - 56",
    "city": "Medellín, Antioquia, Colombia",
    "opening_hours": {
        "weekdays": "Lunes a viernes: 9:00 a. m. a 6:00 p. m. (hora Colombia)",
        "weekends": "No disponible"
    },
    "map_search_url": "https://www.google.com/maps/search/?api=1&query=CR+28B+%23+38F+-+56%2C+Medell%C3%ADn%2C+Colombia"
}

_CONTENT = {
    "hero_title": "Sabores naturales que cuentan historias",
    "hero_description": "Postres artesanales, snacks nutritivos y bebidas seleccionadas con el sabor de nuestras raíces colombianas.",
    "about_us": "En Neifit reunimos sabores tradicionales, frutas y opciones para acompañar distintos momentos del día. Queremos que comprar sea una experiencia cercana y sencilla.",
    "mission": "Ofrecer una selección de postres, snacks y bebidas con atención cálida, información transparente y respeto por los sabores regionales.",
    "vision": "Ser una marca colombiana reconocida por conectar tradición, variedad y una experiencia de compra confiable."
}

_VALUES = [
    {"id": "val-1", "title": "Calidad", "description": "Cuidamos rigurosamente la frescura y calidad de cada insumo.", "sort_order": 1},
    {"id": "val-2", "title": "Transparencia", "description": "Ingredientes claros, precios sin sorpresas.", "sort_order": 2},
    {"id": "val-3", "title": "Cercanía", "description": "Atención personalizada directa por WhatsApp.", "sort_order": 3},
    {"id": "val-4", "title": "Innovación", "description": "Recetas clásicas colombianas reinventadas saludablemente.", "sort_order": 4},
    {"id": "val-5", "title": "Responsabilidad", "description": "Buenas prácticas higiénicas y empaques amigables.", "sort_order": 5},
    {"id": "val-6", "title": "Tradición", "description": "Celebramos el patrimonio gastronómico regional.", "sort_order": 6},
]


@router.get("/configuracion")
@router.get("/settings", deprecated=True)
async def get_settings():
    """Configuración pública del negocio (contacto, horarios)."""
    if database_enabled():
        return await site_repository.settings()
    return {**_SETTINGS, 'shipping_cost': 5000}


@router.put("/configuracion")
@router.put("/settings", deprecated=True)
async def update_settings(data: dict, admin=Depends(require_permission('content.manage'))):
    """Actualizar configuración. Solo administradores."""
    # En producción esto persiste en Supabase tabla company_settings
    if database_enabled():
        return await site_repository.update_settings(data)
    _SETTINGS.update(data)
    return _SETTINGS


@router.get("/contenido")
@router.get("/content", deprecated=True)
async def get_content():
    """Contenido institucional publicado (misión, visión, quiénes somos)."""
    return await site_repository.content() if database_enabled() else _CONTENT


@router.put("/contenido")
@router.put("/content", deprecated=True)
async def update_content(data: dict, admin=Depends(require_permission('content.manage'))):
    """Actualizar contenido institucional. Solo administradores."""
    # En producción persiste en Supabase tabla site_content
    if database_enabled():
        return await site_repository.update_content(data, admin)
    _CONTENT.update(data)
    return _CONTENT


@router.get("/valores")
@router.get("/values", deprecated=True)
async def get_values():
    """Valores corporativos publicados."""
    return await site_repository.values() if database_enabled() else _VALUES


@router.put("/valores")
@router.put("/values", deprecated=True)
async def update_values(data: list, admin=Depends(require_permission('content.manage'))):
    """Actualizar valores. Solo administradores."""
    global _VALUES
    if database_enabled():
        return await site_repository.update_values(data)
    _VALUES = data
    return _VALUES


"""
ProductService — Supabase REST cuando existe configuración de servidor.
Los ejemplos solo se usan sin Supabase configurado; nunca como fallback de errores.
"""
from typing import List, Optional
from datetime import datetime
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.core.supabase_rest import database_enabled
from app.services.commerce_repository import commerce


MOCK_PRODUCTS = [
    {"id":"prod-1","category_id":"cat-1","category_slug":"postres","category_name":"Postres","name":"Postre de Maracuyá Saludable","slug":"postre-de-maracuya-saludable","description":"Esponjosa crema ligera de maracuyá colombiano.","price":12500,"stock":24,"is_available":True,"featured":True,"image_url":"/images/postre-maracuya.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-2","category_id":"cat-1","category_slug":"postres","category_name":"Postres","name":"Mousse Natural de Mango","slug":"mousse-natural-de-mango","description":"Cremoso postre a base de pulpa fresca de mango Tommy.","price":13000,"stock":18,"is_available":True,"featured":True,"image_url":"/images/mousse-mango.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-3","category_id":"cat-1","category_slug":"postres","category_name":"Postres","name":"Delicia de Fresa y Frutos Rojos","slug":"delicia-de-fresa-y-frutos-rojos","description":"Fresas frescas en coulis aromático con crema de coco.","price":13500,"stock":15,"is_available":True,"featured":False,"image_url":"/images/postre-fresa.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-4","category_id":"cat-1","category_slug":"postres","category_name":"Postres","name":"Postre de Melocotón Dorado","slug":"postre-de-melocoton-dorado","description":"Capas de melocotón con yogur griego natural y canela.","price":12800,"stock":12,"is_available":True,"featured":False,"image_url":"/images/postre-melocoton.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-5","category_id":"cat-1","category_slug":"postres","category_name":"Postres","name":"Torta Húmeda de Chontaduro","slug":"torta-humeda-de-chontaduro","description":"Masa suave con pulpa auténtica de chontaduro y coco.","price":14500,"stock":10,"is_available":True,"featured":True,"image_url":"/images/torta-chontaduro.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-6","category_id":"cat-1","category_slug":"postres","category_name":"Postres","name":"Postre Tradicional Regional","slug":"postre-tradicional-regional","description":"Inspirado en arequipe de leche de almendras.","price":14000,"stock":0,"is_available":False,"featured":False,"image_url":"/images/postre-regional.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-7","category_id":"cat-2","category_slug":"snacks","category_name":"Snacks","name":"Cocadas Artesanales sin Azúcar","slug":"cocadas-artesanales-sin-azucar","description":"Coco rallado tostado con panela orgánica de caña.","price":8500,"stock":30,"is_available":True,"featured":True,"image_url":"/images/cocadas.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-8","category_id":"cat-2","category_slug":"snacks","category_name":"Snacks","name":"Dátiles Medjool con Crema de Maní","slug":"datiles-rellenos-crema-mani","description":"Dátiles carnosos rellenos de mantequilla de maní natural.","price":11000,"stock":22,"is_available":True,"featured":True,"image_url":"/images/datiles-mani.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-9","category_id":"cat-2","category_slug":"snacks","category_name":"Snacks","name":"Maní Tostado Natural al Horno","slug":"mani-tostado-natural","description":"Maní tostado con sal rosada de montaña. Sin aceites añadidos.","price":6000,"stock":45,"is_available":True,"featured":False,"image_url":"/images/mani-tostado.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-10","category_id":"cat-2","category_slug":"snacks","category_name":"Snacks","name":"Mix de Frutos Secos y Semillas","slug":"mix-frutos-secos-semillas","description":"Almendras, nueces, semillas de calabaza y arándanos.","price":12000,"stock":25,"is_available":True,"featured":False,"image_url":"/images/mix-frutos-secos.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-11","category_id":"cat-3","category_slug":"bebidas","category_name":"Bebidas","name":"Bebida Fuxion Prunex 1","slug":"fuxion-prunex-1","description":"Té herbal nutracéutico con sabor a ciruela y extracto de linaza para bienestar digestivo.","price":22000,"stock":14,"is_available":True,"featured":True,"image_url":"/images/bebidas-ilustrativas.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-12","category_id":"cat-3","category_slug":"bebidas","category_name":"Bebidas","name":"Bebida Fuxion Flora Liv","slug":"fuxion-flora-liv","description":"Bebida sabor a granadilla con cultivo probiótico y fibra prebiótica.","price":24000,"stock":16,"is_available":True,"featured":True,"image_url":"/images/bebidas-ilustrativas.png","created_at":datetime.now(),"updated_at":datetime.now()},
    {"id":"prod-13","category_id":"cat-3","category_slug":"bebidas","category_name":"Bebidas","name":"Bebida Fuxion Vita Xtra T+","slug":"fuxion-vita-xtra-t","description":"Bebida antioxidante con extractos de maíz morado, camu camu y ginseng.","price":25000,"stock":8,"is_available":True,"featured":False,"image_url":"/images/bebidas-ilustrativas.png","created_at":datetime.now(),"updated_at":datetime.now()},
]


class ProductService:
    def __init__(self):
        self._data = {p["id"]: p for p in MOCK_PRODUCTS}

    async def list_products(
        self, category=None, search=None, featured=None, available=None, include_inactive=False
    ) -> List[dict]:
        if database_enabled():
            return await commerce.products(category, search, featured, available, include_inactive)
        items = list(self._data.values())
        if category:
            items = [p for p in items if p["category_slug"] == category or p["category_id"] == category]
        if search:
            q = search.lower()
            items = [p for p in items if q in p["name"].lower() or q in (p["description"] or "").lower()]
        if featured is not None:
            items = [p for p in items if p["featured"] == featured]
        if available is not None:
            items = [p for p in items if p["is_available"] == available]
        return items

    async def get_by_slug(self, slug: str, include_inactive=False) -> Optional[dict]:
        if database_enabled():
            return await commerce.product(slug, include_inactive)
        for p in self._data.values():
            if p["slug"] == slug or p["id"] == slug:
                return p
        return None

    async def create(self, data: ProductCreate, user=None) -> dict:
        if database_enabled():
            return await commerce.save_product(data, user)
        import uuid
        product_id = str(uuid.uuid4())
        slug = data.slug or data.name.lower().replace(" ", "-").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
        product = {
            **data.model_dump(),
            "id": product_id,
            "slug": slug,
            "is_available": data.is_available if data.is_available is not None else data.stock > 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        self._data[product_id] = product
        return product

    async def update(self, product_id: str, data: ProductUpdate, user=None) -> Optional[dict]:
        if database_enabled():
            return await commerce.save_product(data, user, product_id)
        if product_id not in self._data:
            return None
        product = self._data[product_id].copy()
        updates = data.model_dump(exclude_none=True)
        product.update(updates)
        if "stock" in updates:
            product["is_available"] = updates["stock"] > 0
        product["updated_at"] = datetime.now()
        self._data[product_id] = product
        return product

    async def delete(self, product_id: str, user=None) -> bool:
        if database_enabled():
            return await commerce.deactivate_product(product_id, user)
        if product_id in self._data:
            del self._data[product_id]
            return True
        return False


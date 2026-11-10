from typing import List, Optional
import uuid
from datetime import datetime
from app.schemas.category import CategoryCreate


MOCK_CATEGORIES = [
    {"id":"cat-1","name":"Postres","slug":"postres","description":"Postres saludables elaborados con frutas naturales e inspiración regional.","image":"/images/postre-maracuya.png","is_active":True},
    {"id":"cat-2","name":"Snacks","slug":"snacks","description":"Bocados prácticos, dátiles, cocadas artesanales y frutos secos.","image":"/images/cocadas.png","is_active":True},
    {"id":"cat-3","name":"Bebidas","slug":"bebidas","description":"Bebidas nutracéuticas Fuxion seleccionadas.","image":"/images/bebidas-ilustrativas.png","is_active":True},
]


class CategoryService:
    def __init__(self):
        self._data = {c["id"]: c for c in MOCK_CATEGORIES}

    async def list_active(self) -> List[dict]:
        return [c for c in self._data.values() if c["is_active"]]

    async def create(self, data: CategoryCreate) -> dict:
        cid = str(uuid.uuid4())
        cat = {**data.model_dump(), "id": cid}
        self._data[cid] = cat
        return cat


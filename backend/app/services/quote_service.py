from app.core.permissions import has_permission
from typing import List
import uuid
from datetime import datetime
from app.schemas.quote import QuoteCreate

MOCK_QUOTES = [
    {
        "id": "quot-101",
        "quote_number": "COT-2026-001",
        "customer_name": "Empresa Salud & Bienestar SAS",
        "customer_phone": "+57 315 4443322",
        "customer_email": "bienestar@empresa.com",
        "status": "pendiente",
        "notes": "Cotización para refrigerio corporativo de 40 personas.",
        "items": [
            {"product_id":"prod-7","product_name":"Cocadas Artesanales sin Azúcar","quantity":40,"reference_price":8500},
            {"product_id":"prod-13","product_name":"Bebida Fuxion Vita Xtra T+","quantity":40,"reference_price":25000},
        ],
        "created_at": datetime(2026, 11, 1, 9, 15),
    }
]

class QuoteService:
    def __init__(self):
        self._data = {q["id"]: q for q in MOCK_QUOTES}
        self._counter = len(MOCK_QUOTES) + 1

    async def list_for_user(self, user: dict) -> List[dict]:
        if has_permission(user, 'quotes.manage'):
            return sorted(self._data.values(), key=lambda q: q["created_at"], reverse=True)
        uid = user.get("id")
        return [q for q in self._data.values() if has_permission(user, 'quotes.read_own') and q.get("user_id") == uid]

    async def create(self, data: QuoteCreate, user: dict) -> dict:
        qid = str(uuid.uuid4())
        quote_number = f"COT-2026-{self._counter:03d}"
        self._counter += 1
        quote = {
            "id": qid,
            "user_id": user["id"],
            "quote_number": quote_number,
            "customer_name": data.customer_name,
            "customer_phone": data.customer_phone,
            "customer_email": data.customer_email,
            "status": "pendiente",
            "notes": data.notes,
            "items": [i.model_dump() for i in data.items],
            "created_at": datetime.now(),
        }
        self._data[qid] = quote
        return quote


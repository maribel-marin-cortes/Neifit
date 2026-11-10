from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.core.config import settings
import httpx
from app.core.supabase_rest import supabase_rest
from app.core.operations import request_log, validate_production
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production(settings)
    request_logger = logging.getLogger('neifit.requests')
    request_logger.setLevel(logging.INFO)
    if not request_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        request_logger.addHandler(handler)
    request_logger.propagate = False
    supabase_rest.client = httpx.AsyncClient(timeout=20)
    print("🌿 Neifit API iniciando...")
    yield
    await supabase_rest.client.aclose()
    supabase_rest.client = None
    print("🌿 Neifit API detenida.")

app = FastAPI(
    title="Neifit API",
    description="API para la tienda virtual Neifit — postres, snacks y bebidas saludables.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV != 'production' else None,
    redoc_url="/redoc" if settings.APP_ENV != 'production' else None,
)

app.middleware('http')(request_log)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=['X-Auth-Error', 'X-Request-ID'],
)

# Incluir routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Neifit API activa",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@app.get('/ready', tags=['Health'])
async def readiness_check():
    await supabase_rest.request('GET', 'notifications', params={'select': 'id', 'limit': '0'})
    await supabase_rest.request('GET', 'customer_addresses', params={'select': 'id', 'limit': '0'})
    return {'status': 'ready'}


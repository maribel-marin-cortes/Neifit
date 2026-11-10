from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_JWT_ISSUER: str = ""
    SUPABASE_JWKS_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""  # Solo backend, NUNCA en frontend

    # Database (Supabase PostgreSQL)
    DATABASE_URL: str = ""

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # App
    APP_ENV: str = "development"
    ENABLE_DEMO_AUTH: bool = False
    RBAC_DATABASE_ENABLED: bool = False
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True

    # Pagos (solo backend, nunca exponer en frontend)
    WOMPI_SECRET_KEY: str = ""
    MERCADOPAGO_ACCESS_TOKEN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


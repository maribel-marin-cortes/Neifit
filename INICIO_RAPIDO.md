# Neifit — Inicio rápido

## Estructura del proyecto

## Arranque local configurado

Desde la raíz, abrir dos terminales PowerShell:

```powershell
# Terminal 1
.\iniciar-backend.ps1 -Demo
# Terminal 2
.\iniciar-frontend.ps1
```

Aplicación: http://127.0.0.1:5173. API: http://127.0.0.1:8000/docs. Detener cada servicio con Ctrl+C.

Python 3.12.12 está instalado en `.python/` y el entorno operativo está en `backend/.venv/`. El entorno antiguo `backend/venv/` no se usa. Los scripts fijan `DEBUG=true` para evitar conflicto con la variable `DEBUG=release` heredada del sistema. El backend habilita acceso demo únicamente en desarrollo y sin Supabase configurado.

Pruebas desde `backend/`: `$env:DEBUG='true'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`.

Para instalar la base y conectar cuentas reales, sigue `CONEXION_SUPABASE.md`. El SQL completo está en `supabase/neifit_inicial.sql`. Con Supabase configurado ejecuta `.\iniciar-backend.ps1` sin `-Demo`. Las pruebas de la API del frontend se ejecutan desde `frontend/` con `npm test`.

Verificado el 1 de noviembre de 2026: compilación frontend correcta y 8 pruebas de backend aprobadas.

## Instalación desde cero
```
proyecto_neifit/
├── frontend/          # React + Vite + Tailwind CSS
└── backend/           # Python + FastAPI
```

## Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Backend

```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Variables de entorno

- **frontend/.env** — copiar de `.env.example` y completar con credenciales Supabase
- **backend/.env** — copiar de `.env.example` y completar con credenciales Supabase

> Para las dependencias fijadas del backend, usar Python 3.12. Ya se creó un entorno compatible en `backend/.venv/`.
>
> El proyecto incluye un modo **mock/local**. Para habilitar tokens demo en la API se requiere `APP_ENV=development`, `ENABLE_DEMO_AUTH=true` y dejar vacías `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`, `SUPABASE_JWKS_URL` y `SUPABASE_SERVICE_ROLE_KEY`. Por defecto están deshabilitados. No activar este modo en un servidor público.
> Los datos demo se cargan automáticamente desde `mockData.js` y los servicios del backend.

## Roles demo (acceso rápido)

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Admin | admin@neifit.com | cualquiera |
| Mensajería | mensajeria@neifit.com | cualquiera |
| Cliente | cliente@neifit.com | cualquiera |

O usa los botones de acceso rápido en la pantalla de Login.

## Autenticación real y comprobaciones

La API valida firma RS256/ES256, emisor, audiencia, caducidad e identificador del JWT. Consulta el rol en `profiles` mediante Supabase REST; no acepta el rol de `user_metadata`. Se necesitan las cuatro variables Supabase del backend y una tabla `profiles` con permisos que impidan al cliente modificar su rol. La clave `SUPABASE_SERVICE_ROLE_KEY` permanece exclusivamente en el backend.

Desde `backend/`, ejecutar `python -m unittest discover -s tests -v`. Las pruebas usan servicios simulados y no requieren credenciales reales.

Con Supabase configurado, los módulos comerciales usan las tablas y RPC reales y no sustituyen errores por datos de demostración. Ejecuta `supabase/activar_servicios_supabase.sql` en una base existente y sigue **PERSISTENCIA_SUPABASE.md**. Sin configuración de Supabase se mantiene el modo de demostración. El carrito sigue local y los pagos nuevos quedan pendientes; no se simula la confirmación de una pasarela.


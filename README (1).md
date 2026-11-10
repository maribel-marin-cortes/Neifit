# Neifit

Tienda virtual de productos saludables inspirados en sabores tradicionales y naturales de Colombia.

## 1. Descripción general

**Neifit** es una tienda virtual enfocada en la venta de:

- **Postres saludables** con sabores de maracuyá, mango, fresa, melocotón y chontaduro.
- **Postres tradicionales por región**, reinterpretados en una línea más saludable.
- **Snacks naturales** como cocadas, dátiles, maní y frutos secos.
- **Bebidas nutracéuticas Fuxion**.

El proyecto busca ofrecer una experiencia de compra sencilla, visualmente cálida y confiable, con trazabilidad del pedido y contacto directo por WhatsApp.

## 2. Objetivo del proyecto

Desarrollar una plataforma web moderna que permita:

- Exhibir el catálogo de productos.
- Gestionar compras en línea.
- Controlar disponibilidad e inventario.
- Generar pedidos o guías de despacho para trazabilidad.
- Integrar medios de contacto y pagos.

## 3. Alcance del MVP

El producto mínimo viable (MVP) incluirá:

- Página de inicio.
- Catálogo de productos por categorías.
- Vista detalle de producto.
- Carro de compras.
- Registro e inicio de sesión.
- Panel de administrador.
- Módulo de inventario y disponibilidad.
- Generación de pedido/guía con número de seguimiento interno.
- Botón de WhatsApp.
- Solicitud de cotización.
- Integración de pasarela de pagos (fase MVP si se cuenta con credenciales; de lo contrario, se deja preparada la estructura).

## 4. Roles del sistema

- **Administrador:** gestiona productos, usuarios, inventario, pedidos, cotizaciones y trazabilidad.
- **Mensajería:** consulta pedidos asignados, estado de entrega y actualiza trazabilidad.
- **Cliente:** navega el catálogo, compra, cotiza, consulta sus pedidos y se comunica por WhatsApp.

## 5. Módulos principales

1. **Catálogo**
2. **Carro de compras**
3. **Usuarios y autenticación**
4. **Inventario y disponibilidad**
5. **Cotizador**
6. **Pedidos y trazabilidad**
7. **Mensajería**
8. **Pasarela de pagos**
9. **Botón de WhatsApp**
10. **Panel administrativo**

## 6. Propuesta de identidad visual

### Concepto de logo

Logo con **ramillete de frutas** que incluya:

- chontaduro,
- coco,
- mango,
- fresas,
- hojas verdes.

El nombre **Neifit** debe ir en **color café**, transmitiendo naturalidad, cercanía y un enfoque artesanal.

### Recomendación de color para la web

Se recomiendan tres líneas base:

#### Opción recomendada (equilibrada)
- Fondo cálido claro: `#F6E7D8`
- Café principal: `#7A4E2D`
- Verde hoja: `#5F8D4E`
- Rosa acento: `#D98CA4`
- Crema suave: `#FFF8F2`

**Ventaja:** comunica naturalidad, dulzura y salud sin perder contraste.

#### Opción 2 (más femenina y suave)
- Rosa suave: `#F7D6E0`
- Café medio: `#8B5E3C`
- Verde hoja: `#6D8B74`
- Marfil: `#FFF9F5`

#### Opción 3 (más natural y orgánica)
- Beige café claro: `#E8D2B0`
- Café oscuro: `#6B4226`
- Verde oliva: `#7D9D6C`
- Melón / coral suave: `#F4B183`

## 7. Stack propuesto

- **Frontend:** React + Vite + JavaScript + Tailwind CSS
- **Backend API:** Python + FastAPI
- **Backend de datos:** Supabase (PostgreSQL, Auth y Storage)
- **Base de datos:** PostgreSQL (Supabase)
- **Autenticación:** Supabase Auth
- **Storage:** Supabase Storage (si se usan imágenes o comprobantes)
- **Pagos:** integración futura con Wompi, Mercado Pago o PayU

## 8. Estructura documental incluida

Este proyecto incluye los siguientes archivos Markdown:

- `README.md`
- `AGENTS.md`
- `DESIGN.md`
- `REQUISITOS.md`
- `DATABASE.md`
- `TAREAS.md`

## 9. Estado actual

Existe una implementación preliminar React/Vite y FastAPI de los módulos principales, con datos demo y persistencia parcial en el navegador. No constituye todavía un MVP conectado a Supabase ni listo para producción. Ver `INICIO_RAPIDO.md` para ejecución y limitaciones.

Actualización del 1 de noviembre de 2026: se restringió la autenticación demo a desarrollo con activación explícita, se añadió validación JWT RS256/ES256 y consulta del rol en `profiles`. Se agregaron pruebas automatizadas de permisos; la validación con Supabase real y las políticas RLS siguen pendientes.

## 10. Siguiente paso sugerido

Usar esta documentación como base para generar el proyecto en Antigravity IDE o en otro entorno de desarrollo con React + Vite + Supabase.


## 11. Landing page corporativa (alcance ampliado)

La ruta pública `/` será una **landing page corporativa y comercial**, distinta de la experiencia de catálogo `/catalogo` y de los paneles privados. Incluirá navegación, portada con logo y fotografías realistas de frutas, quiénes somos, misión, visión, valores, productos destacados, ubicación, contacto y footer legal. Usar únicamente datos reales de dirección, teléfono, horarios y enlaces provistos por el negocio; hasta entonces mostrar campos configurables y no publicar datos de prueba.

**Copy de referencia anterior (sustituido por los textos seleccionados abajo):** «Neifit celebra los sabores tradicionales de Colombia a través de postres, snacks y bebidas seleccionadas, con una experiencia cercana y práctica». Misión: «Ofrecer productos con sabores naturales y tradicionales, priorizando la calidad, la información clara y una atención cercana». Visión: «Consolidarnos como una marca colombiana reconocida por su identidad regional, variedad y servicio confiable». Valores: calidad, transparencia, cercanía, innovación, responsabilidad y respeto por las tradiciones.

**Arquitectura actualizada:** React + Vite + JavaScript + Tailwind CSS en frontend; Python 3.12+ + FastAPI + Pydantic para la API; Supabase PostgreSQL, Auth y Storage para persistencia. React consume endpoints `/api/v1/`; FastAPI verifica JWT de Supabase, aplica permisos por rol y valida inventario, pedidos, cotizaciones y pagos. La pasarela se conectará por backend y verificará webhooks; nunca confiar en el éxito declarado por el navegador.

**Rutas sugeridas:** `/`, `/catalogo`, `/productos/:slug`, `/carrito`, `/cotizador`, `/checkout`, `/mi-cuenta`, `/mis-pedidos`, `/seguimiento/:codigo`, `/admin/*`, `/mensajeria/*`.

**Estructura sugerida:** `frontend/` y `backend/` con `backend/app/main.py`, `api/`, `schemas/`, `services/`, `repositories/`, `core/`, `tests/`; `supabase/migrations/` para SQL y `public/` para identidad visual. No almacenar claves privadas en frontend.

**Variables orientativas:** frontend `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`; backend `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`, `SUPABASE_JWKS_URL`, `DATABASE_URL` y credenciales de pagos solo en entorno seguro. Documentar `.env.example` ficticios y excluir archivos `.env` de git.


## 12. Configuración de la landing page — datos confirmados

## Datos comerciales confirmados para la landing page

- **Ciudad:** Medellín, Antioquia, Colombia.
- **Dirección:** CR 28B # 38F - 56.
- **Teléfono y WhatsApp:** +57 3127827020.
- **Enlace WhatsApp:** https://wa.me/573127827020.
- **Horario de atención:** lunes a viernes, 9:00 a. m. a 6:00 p. m. (hora Colombia).
- **Fin de semana:** horario no informado; no mostrar horas inventadas.
- **Mapa:** vincular la búsqueda por la dirección facilitada; no mostrar coordenadas no verificadas.

## Textos institucionales seleccionados (editables)

**Quiénes somos:** En Neifit reunimos sabores tradicionales, frutas y opciones para acompañar distintos momentos del día. Queremos que comprar sea una experiencia cercana y sencilla.

**Misión:** Ofrecer una selección de postres, snacks y bebidas con atención cálida, información transparente y respeto por los sabores regionales.

**Visión:** Ser una marca colombiana reconocida por conectar tradición, variedad y una experiencia de compra confiable.

**Valores:** Calidad, transparencia, cercanía, innovación, responsabilidad y tradición.

Estos textos son propuestas de comunicación elegidas por el usuario para la landing, no aseveraciones sobre certificaciones, origen comprobado o propiedades médicas.

# AGENTS.md

## Reglas permanentes para el desarrollo de Neifit

Este archivo define las reglas que cualquier agente o desarrollador debe seguir al trabajar en **Neifit**.

## 1. Lectura obligatoria antes de modificar el proyecto

Antes de realizar cualquier cambio se debe leer, en este orden:

1. `REQUISITOS.md`
2. `DATABASE.md`
3. `DESIGN.md`
4. `TAREAS.md`
5. `README.md`

## 2. Objetivo del sistema

Construir una tienda virtual saludable para exhibir y vender postres, snacks y bebidas, con control de inventario, carrito de compras, pedidos, cotizaciones y trazabilidad de entrega.

## 3. Pila tecnológica obligatoria

- **Frontend:** React + Vite + JavaScript (sin TypeScript) + Tailwind CSS
- **Ruteo:** React Router DOM
- **Estilos:** CSS Modules, CSS plano o Tailwind solo si aporta valor real
- **Backend API:** Python + FastAPI + Pydantic
- **BaaS:** Supabase
- **Base de datos:** PostgreSQL
- **Auth:** Supabase Auth
- **Archivos:** Supabase Storage si es necesario

## 4. Módulos autorizados

Se pueden implementar únicamente los siguientes módulos, salvo autorización posterior:

1. Catálogo
2. Carro de compras
3. Usuarios y autenticación
4. Panel administrativo
5. Inventario y disponibilidad
6. Cotizador
7. Pedidos y trazabilidad
8. Mensajería
9. Pasarela de pagos
10. Botón de WhatsApp

## 5. Roles del sistema

- **Administrador**
- **Mensajería**
- **Cliente**

Ningún usuario podrá modificar directamente su propio rol.

## 6. Reglas funcionales clave

- Los productos se agrupan por categorías: **Postres**, **Snacks** y **Bebidas**.
- Los productos deben mostrar disponibilidad.
- Si un producto no tiene stock, se debe indicar como no disponible.
- El cliente puede agregar productos al carro, cotizar y generar pedido.
- Todo pedido debe contar con un identificador único para trazabilidad.
- El rol de mensajería solo puede consultar o actualizar el estado logístico de pedidos asignados.
- El botón de WhatsApp debe estar visible en áreas clave.

## 7. Reglas de desarrollo

- Mantener arquitectura limpia y componentes reutilizables.
- No crear archivos gigantes ni duplicar lógica.
- Implementar estados de carga, vacío, éxito y error.
- Usar nombres claros en español o consistentes si se define convención en inglés técnico.
- Todo cambio importante debe reflejarse en la documentación.

## 8. Seguridad

- Nunca exponer claves secretas en frontend.
- Solo usar `VITE_SUPABASE_URL` y `VITE_SUPABASE_PUBLISHABLE_KEY`.
- Habilitar RLS en tablas privadas.
- No usar políticas abiertas para información sensible.
- Proteger operaciones por rol.

## 9. Definición de terminado

Una tarea se considera terminada solo si:

- funciona,
- fue verificada manualmente,
- mantiene coherencia con la documentación,
- y queda marcada en `TAREAS.md`.

## 10. Lineamiento visual de marca

El diseño debe respetar:

- Logo con frutas (chontaduro, coco, mango, fresas y hojas verdes).
- Nombre **Neifit** en color café.
- Estética cálida, natural, saludable y artesanal.
- Contraste suficiente para legibilidad.


## 11. Landing page corporativa — obligatoria

- Construir una página pública en `/` con Hero, Quiénes somos, Misión, Visión, Valores, productos destacados, Ubicación, Teléfono/WhatsApp y Footer.
- Toda la información institucional debe ser editable por el administrador, salvo contenido legal que debe aprobarse antes de publicarse.
- No inventar dirección, teléfono, historia de la marca, testimonios, certificaciones ni beneficios médicos.
- El logo debe mostrar **frutas de apariencia realista** (chontaduro, coco, mango, fresas y hojas verdes) y el nombre Neifit café. No usar frutas caricaturizadas. Para implementación se requiere un activo aprobado en PNG/WebP/SVG según corresponda.
- Priorizar contraste AA WCAG para texto, navegación por teclado y etiquetas accesibles.

## 12. Contrato frontend–backend

- Frontend solo consume la API FastAPI para reglas comerciales; Supabase Auth puede gestionar inicio de sesión desde el cliente usando clave pública.
- Backend comprueba los tokens, permisos del usuario, stock y el importe de pedido antes de operaciones sensibles.
- Nunca escribir `service_role`, secretos de pagos o cadena privada `DATABASE_URL` en `VITE_*`.
- Generar confirmaciones de pago exclusivamente tras verificar webhooks firmados del proveedor.
- Usar transacciones en PostgreSQL para reservas/descuentos de inventario y evitar sobreventa.
- Mantener documentación y pruebas alineadas al modificar el alcance.


## 12. Configuración confirmada de Neifit

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

Al implementar la landing, tomar estos datos como contenido inicial, no como variables ficticias. No publicar coordenadas de mapa sin verificarlas.

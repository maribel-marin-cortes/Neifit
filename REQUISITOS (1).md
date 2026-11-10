# REQUISITOS.md

# Requisitos del proyecto Neifit

## Actualización de acceso solicitada por el usuario

La landing institucional y una muestra de productos son públicas. Los módulos comerciales completos requieren sesión; seleccionar un producto lleva a login/registro y se conserva el destino para después del acceso. Login y registro son pantallas independientes sin sidebar de módulos. Los clientes acceden a compras y pedidos propios, mensajería a asignados y administración a sus módulos por rol. La API también comprueba permisos; no basta con ocultar enlaces. Esta actualización sustituye los criterios anteriores de catálogo completo y seguimiento sin registro. Ver `PLAN_AUTORIZACION.md`.

## 1. Objetivo general

Desarrollar una tienda virtual para la venta de productos saludables de la marca **Neifit**, con control de inventario, gestión de pedidos, cotizaciones y trazabilidad.

## 2. Actores del sistema

### 2.1 Administrador
Puede:
- gestionar productos,
- gestionar categorías,
- gestionar inventario,
- gestionar usuarios,
- revisar pedidos,
- gestionar cotizaciones,
- consultar trazabilidad,
- configurar contenido general del sitio.

### 2.2 Mensajería
Puede:
- ver pedidos asignados,
- consultar datos logísticos,
- actualizar estados del pedido,
- registrar novedades,
- confirmar entrega.

### 2.3 Cliente
Puede:
- navegar catálogo,
- ver productos,
- agregarlos al carrito,
- cotizar,
- comprar,
- pagar,
- consultar pedidos,
- ver trazabilidad,
- comunicarse por WhatsApp.

## 3. Módulos funcionales

### 3.1 Catálogo
Debe permitir:
- listar productos,
- filtrar por categoría,
- buscar productos,
- mostrar disponibilidad,
- visualizar detalle.

### 3.2 Carro de compras
Debe permitir:
- agregar productos,
- modificar cantidades,
- eliminar productos,
- calcular totales,
- iniciar proceso de pago o cotización.

### 3.3 Usuarios
Debe contemplar:
- registro,
- inicio de sesión,
- recuperación de acceso,
- perfil básico,
- control por roles.

### 3.4 Pasarela de pagos
Debe permitir integrar una pasarela para:
- pago de pedidos,
- confirmación del pago,
- actualización del estado del pedido.

### 3.5 Inventario y disponibilidad
Debe permitir:
- definir stock por producto,
- marcar disponibilidad,
- descontar stock con pedidos confirmados,
- alertar productos agotados.

### 3.6 Cotizador
Debe permitir:
- solicitar cotización de uno o varios productos,
- registrar datos del cliente,
- generar respuesta comercial.

### 3.7 Botón de WhatsApp
Debe estar disponible para:
- atención comercial,
- dudas del cliente,
- apoyo al proceso de compra.

### 3.8 Generador de guía o pedido
Debe permitir:
- crear número interno de pedido,
- generar guía o referencia logística,
- consultar el estado del pedido,
- dar trazabilidad del proceso.

### 3.9 Mensajería
Debe permitir:
- consultar pedidos asignados,
- actualizar estado,
- registrar entrega o novedad.

## 4. Categorías del catálogo

- **Postres**
- **Snacks**
- **Bebidas**

## 5. Productos base mencionados

### 5.1 Postres
- Maracuyá
- Mango
- Fresa
- Melocotón
- Chontaduro
- Postres tradicionales de cada región

### 5.2 Snacks
- Cocadas
- Dátiles
- Maní
- Frutos secos

### 5.3 Bebidas
- Productos Fuxion nutracéuticos

## 6. Reglas de negocio principales

1. Cada producto pertenece a una categoría.
2. Cada producto debe tener disponibilidad visible.
3. Un pedido debe asociarse a un cliente.
4. Todo pedido debe tener un estado.
5. Todo pedido debe tener trazabilidad.
6. El inventario debe reflejar disponibilidad real.
7. Solo el administrador puede crear o editar productos.
8. El personal de mensajería no puede editar productos ni precios.
9. El cliente no puede ver pedidos de otros clientes.
10. La integración de pagos debe actualizar el estado del pedido cuando aplique.

## 7. Requisitos no funcionales

- Interfaz responsive.
- Buen contraste visual.
- Navegación simple.
- Mensajes claros al usuario.
- Seguridad basada en roles.
- Escalabilidad para agregar nuevos productos.

## 8. Criterios de aceptación del MVP

El MVP se considera aceptado si:

- el catálogo funciona,
- el carrito funciona,
- los roles están diferenciados,
- se puede registrar y consultar un pedido,
- el inventario muestra disponibilidad,
- existe trazabilidad básica,
- el administrador puede gestionar el catálogo,
- el cliente puede contactar por WhatsApp.


## 9. Landing page institucional y contenido administrable

### RF-LP-01 Página pública
El visitante accede sin iniciar sesión a `/`, con Hero, logo realista, presentación de marca, misión, visión, valores, categorías, ubicación y contacto.

### RF-LP-02 Quiénes somos
Mostrar texto corporativo gestionado por el administrador; no afirmar historia o experiencia no documentadas.

### RF-LP-03 Misión, visión y valores
El administrador puede editar estos contenidos; las páginas muestran la última versión publicada. Proponer textos iniciales en `DESIGN.md`, pero requieren aprobación.

### RF-LP-04 Ubicación y teléfono
Publicar solo dirección, ciudad, teléfono y horarios proporcionados por el negocio. Un botón abre WhatsApp al número configurado y validado; un mapa solo aparece cuando existe ubicación verificable.

### RF-LP-05 Navegación
Enlaces al catálogo, carrito, cotizador y seguimiento desde la landing. Diseño responsive y accesible.

### RF-LP-06 Contenido y cumplimiento
No afirmar que productos previenen, tratan o curan enfermedades; las descripciones nutracéuticas de Fuxion deben basarse en información oficial y aprobada para comercialización. Informar ingredientes, alérgenos, precios y condiciones de entrega.

## 10. Arquitectura y reglas de backend Python

- API FastAPI bajo prefijo `/api/v1` para productos, inventario, cotizaciones, pedidos, seguimiento, contenido institucional y webhook de pagos.
- JWT expedidos por Supabase Auth validados en backend.
- Roles administrador, mensajería y cliente verificados en la API y en las políticas de base de datos.
- El frontend nunca define el valor definitivo de un pedido ni descuenta inventario por sí solo.
- El backend debe realizar pedidos y modificaciones de stock de manera atómica para impedir compras de productos agotados.
- Estados de pago actualizados solo por respuesta verificada del proveedor.

## 11. Criterios de aceptación adicionales

- El usuario puede leer «Quiénes somos», misión, visión y valores sin registro.
- Los botones hacia catálogo, WhatsApp y contacto funcionan en móvil y escritorio.
- Si faltan datos de ubicación y teléfono, no aparecen falsos datos como definitivos.
- El administrador puede editar y publicar contenidos institucionales.
- La API deniega edición institucional a clientes y mensajeros.


## 10. Datos institucionales confirmados para aceptación

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

**Criterios añadidos:** mostrar los datos anteriores en Contacto y footer, usar el enlace de WhatsApp con formato `wa.me`, no inventar coordenadas, permitir al administrador actualizar los textos de misión/visión/valores y los datos comerciales.

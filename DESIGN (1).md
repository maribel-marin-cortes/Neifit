# DESIGN.md

# Sistema de diseño e identidad visual de Neifit

## Separación entre landing, acceso y módulos

La landing conserva encabezado y footer institucionales para visitantes, sin sidebar ni accesos directos al carrito. Login, registro y recuperación son pantallas independientes. El layout con sidebar desplegable se utiliza para usuarios con sesión. Al seleccionar productos desde la muestra pública se solicita acceso o registro conservando el destino del producto. Este criterio sustituye la inclusión anterior del layout de módulos en autenticación. Ver `PLAN_AUTORIZACION.md`.

## Logo vigente: Sabores Tropicales Saludables

Por solicitud explícita del usuario, se reemplaza el logo anterior por `frontend/public/logo-neifit-tropical.png`, copia sin modificaciones del archivo «Neifit_ Sabores Tropicales Saludables.png» suministrado. Incluye frutas realistas, letras naranja/verde y el fondo decorativo del original. Esta selección sustituye las decisiones anteriores de logo café y versión transparente; no modifica la paleta general de la interfaz. Se actualizan encabezado, portada, footer, login, recuperación de contraseña, callback Google y favicon. Los activos anteriores permanecen conservados.

## Estructura vigente de página: encabezado, sidebar, contenido y footer

Actualización: el sidebar es desplegable mediante el botón de menú del encabezado tanto en escritorio como en móvil. Comienza cerrado; el clic alterna abrir/cerrar, y al cerrarlo el contenido recupera todo el ancho. También se cierra al navegar o pulsar Escape. Esto sustituye la visibilidad permanente en escritorio descrita en la primera versión.

La referencia de distribución suministrada por el usuario se implementa mediante `SiteLayout`: encabezado superior de ancho completo; debajo, menú de módulos a la izquierda (240 px en escritorio) y contenido principal flexible a la derecha; footer inferior de ancho completo. Se conserva la paleta Neifit. Esta estructura sustituye la navegación principal horizontal propuesta anteriormente en este documento.

El encabezado contiene logo, contacto WhatsApp, carrito y cuenta. El sidebar contiene Inicio, Catálogo, Postres, Snacks, Bebidas, Carrito, Cotizador, Seguimiento y accesos de cuenta. Administradores ven Resumen, Productos e inventario, Pedidos y Cotizaciones. Mensajería está disponible para personal autorizado. Las rutas siguen protegidas por rol; ocultar un enlace no sustituye los permisos de la API.

El módulo activo se destaca con texto y fondo. En móvil, el botón «Abrir menú de módulos» despliega el menú bajo el encabezado; al navegar o pulsar Escape se cierra. Se incluyen `aria-expanded`, `aria-controls`, `aria-current`, foco visible y enlace para saltar al contenido. El sidebar puede desplazarse en pantallas de poca altura. Las páginas de acceso y los paneles usan la misma estructura.

La navegación administrativa utiliza `?modulo=productos`, `?modulo=pedidos` y `?modulo=cotizaciones`, conservando el estado al recargar y permitiendo usar atrás/adelante del navegador. Las pestañas horizontales anteriores se retiraron para evitar navegación duplicada.

## Imágenes del catálogo y categorías

Los productos demo y categorías usan archivos propios del proyecto en `frontend/public/images/`, sin depender de servidores externos. Las imágenes generadas con imagegen son ilustraciones fotorealistas y llevan indicación «Imagen ilustrativa» en tarjetas, categorías y detalle. La imagen genérica de bebidas no representa envases, formulaciones ni fotografías oficiales de Fuxion. Deben reemplazarse por fotografías aprobadas antes de utilizarlas como representación comercial del producto real.

El componente reutilizable `CatalogImage` mantiene el tamaño de presentación y muestra `/placeholder-product.svg` ante un error de carga, sin volver a asignar indefinidamente una ruta rota. `catalogImages.js` mantiene compatibilidad con las URL antiguas guardadas en el carrito y conserva imágenes personalizadas. La tarjeta reserva una proporción 4:3 y recorta con `object-cover`, sin deformar la fotografía. Los logos conservan su proporción y transparencia.

## Logo proporcionado por el usuario

Actualización: la versión activa es `frontend/public/logo-neifit-transparente.png`, editada con imagegen para eliminar el fondo blanco con canal alfa. Las cinco referencias de la aplicación utilizan esta versión y se retiró `bg-white` del logo de navegación. La imagen original `logo-neifit.png` se conserva como referencia. Esto sustituye la decisión anterior de mantener el fondo blanco.

Se incorporó `frontend/public/logo-neifit.png`, copia exacta de «Logo Neifit con frutas tropicales (1).png». Incluye frutas realistas, nombre Neifit café y las leyendas «Postres · Snacks · Bebidas» y «Saludables y Naturales». Se usa en navegación, portada, inicio de sesión, footer y favicon. Se mantiene su fondo blanco, proporción 3:2 y colores originales; el footer ya no aplica filtros de brillo/contraste al logo. `logo.svg` permanece como archivo preliminar, sin referencias activas en estas vistas.

## 1. Concepto de marca

**Neifit** es una marca de alimentos saludables con una personalidad:

- natural,
- cercana,
- fresca,
- artesanal,
- y alegre.

La identidad debe mezclar el mundo de la nutrición saludable con el atractivo visual de los postres y snacks tradicionales.

## 2. Concepto del logo

### Descripción del logo

El logo debe estar compuesto por:

- un **ramillete de frutas**,
- incluyendo **chontaduro**, **coco**, **mango**, **fresas**,
- acompañado de **hojas verdes**,
- y el nombre **Neifit** en **color café**.

### Significado

- **Frutas:** representan frescura, salud y sabor.
- **Hojas verdes:** reflejan naturalidad.
- **Color café en el nombre:** transmite cercanía, producto artesanal, tierra y confianza.

## 3. Recomendación de paleta de colores

## Opción recomendada principal

| Uso | Color | HEX | Motivo |
|---|---|---|---|
| Fondo principal | Beige cálido claro | `#F6E7D8` | genera calidez y limpieza |
| Color principal | Café medio | `#7A4E2D` | ideal para el nombre y títulos |
| Color secundario | Verde hoja | `#5F8D4E` | comunica naturaleza |
| Acento suave | Rosa frutal | `#D98CA4` | aporta dulzura y armonía |
| Fondo tarjetas | Crema claro | `#FFF8F2` | mejora lectura y contraste |
| Texto oscuro | Café oscuro | `#4B2E1F` | alta legibilidad |

### Recomendación final

La **mejor combinación** para la página es:

- fondo café claro / beige cálido,
- botones y títulos en café,
- detalles y etiquetas en verde,
- acentos suaves en rosado.

Esto da un aspecto saludable, elegante y coherente con el negocio.

## 4. Uso recomendado de color en interfaz

- **Header y footer:** café principal o beige cálido con texto contrastante.
- **Botones primarios:** café principal con texto claro.
- **Botones secundarios:** verde hoja.
- **Etiquetas promocionales:** rosa suave.
- **Fondo general:** crema o beige claro.
- **Tarjetas de producto:** crema con sombras suaves.

## 5. Tipografías sugeridas

### Logo
- Estilo manuscrito o display amigable.

### Títulos
- **Poppins** o **Montserrat** (Semibold / Bold).

### Texto general
- **Inter**, **Nunito** o **Open Sans**.

## 6. Estilo visual

- Bordes redondeados.
- Imágenes limpias y apetitosas.
- Tarjetas con aspecto fresco y ordenado.
- Íconos simples.
- Diseño responsive.

## 7. Componentes principales

### 7.1 Navbar
Debe incluir:
- Logo Neifit
- Inicio
- Catálogo
- Snacks
- Postres
- Bebidas
- Cotizador
- Carro
- Iniciar sesión
- Botón WhatsApp

### 7.2 Hero principal
Debe comunicar:
- alimentación saludable,
- tradición regional,
- ingredientes naturales.

Texto sugerido:

> Postres, snacks y bebidas saludables con el sabor de nuestras raíces.

### 7.3 Tarjeta de producto
Debe mostrar:
- imagen,
- nombre,
- categoría,
- descripción corta,
- precio,
- disponibilidad,
- botón agregar al carrito.

### 7.4 Carro de compras
Debe mostrar:
- productos agregados,
- cantidad,
- subtotal,
- total,
- botón de pagar,
- botón de cotizar,
- botón de finalizar pedido.

### 7.5 Panel administrador
Debe incluir accesos a:
- productos,
- categorías,
- inventario,
- pedidos,
- cotizaciones,
- usuarios,
- trazabilidad.

### 7.6 Panel mensajería
Debe permitir:
- ver pedidos asignados,
- cambiar estado del pedido,
- registrar novedad,
- confirmar entrega.

## 8. Pantallas mínimas sugeridas

1. Inicio
2. Catálogo general
3. Detalle de producto
4. Carro de compras
5. Login / registro
6. Mi cuenta
7. Mis pedidos
8. Cotizador
9. Panel administrador
10. Panel mensajería
11. Seguimiento de pedido / trazabilidad
12. Página de contacto / WhatsApp

## 9. Accesibilidad y contraste

- El texto café oscuro sobre fondo crema o beige ofrece buena legibilidad.
- Evitar rosados demasiado pálidos para texto principal.
- Los botones deben tener suficiente contraste.
- Las etiquetas de disponibilidad deben usar texto e ícono, no solo color.

## 10. Recomendación final de identidad

Para Neifit se recomienda una identidad basada en:

- **café claro / beige** como base,
- **café medio u oscuro** para marca,
- **verde natural** como respaldo saludable,
- **rosado suave** como acento frutal.

Esta combinación ayuda a que la marca se vea:

- confiable,
- cálida,
- femenina sin ser limitada,
- natural,
- y visualmente apetitosa.


## 11. Landing page: diseño y estructura

La landing page debe tener una navegación sticky con logo realista, enlaces «Inicio», «Quiénes somos», «Nuestros productos», «Misión y visión», «Valores», «Ubicación» y «Contacto», además de botones «Ver catálogo» y «WhatsApp». En móvil usar menú accesible.

**Secciones (de arriba hacia abajo):**

1. **Hero:** fondo crema, foto gastronómica realista, título «Sabores naturales que cuentan historias», texto breve y CTA «Explorar catálogo».
2. **Quiénes somos:** presentación de Neifit como emprendimiento; texto editable sin inventar antigüedad o trayectoria.
3. **Misión y visión:** dos bloques de fondo claro y detalles verde hoja; texto editable elegido para la primera versión.
4. **Nuestros valores:** seis tarjetas discretas: calidad, transparencia, cercanía, innovación, responsabilidad y tradición.
5. **Categorías destacadas:** Postres tradicionales, Snacks naturales, Bebidas Fuxion; fotos reales y acceso al catálogo.
6. **Ubicación y contacto:** dirección, ciudad, horario, mapa externo opcional, teléfono y CTA WhatsApp. Mostrar solo datos verificados.
7. **Footer:** marca, enlaces de navegación, política de privacidad, términos, datos comerciales reales y redes autorizadas.

### Copy corporativo inicial — editable

- **Quiénes somos:** «En Neifit reunimos sabores tradicionales, frutas y opciones para acompañar distintos momentos del día. Queremos que comprar sea una experiencia cercana y sencilla».
- **Misión:** «Ofrecer una selección de postres, snacks y bebidas con atención cálida, información transparente y respeto por los sabores regionales».
- **Visión:** «Ser una marca colombiana reconocida por conectar tradición, variedad y una experiencia de compra confiable».
- **Valores:** calidad, transparencia, cercanía, innovación, responsabilidad, tradición.

### Responsividad

- Móvil: contenido en una columna, CTA visible, imágenes optimizadas.
- Tableta: dos columnas para tarjetas.
- Escritorio: hero en dos columnas y secciones con máximo ancho legible.

### Imagen de marca

Prohibidos en el logo final los frutos caricaturescos y los iconos de frutas planos. Utilizar un ramillete **fotorealista**, con coco abierto, mango, fresas, chontaduro y hojas verdes; nombre Neifit café `#7A4E2D`. El SVG vectorial preliminar existente no se considera logo final aprobado.


## 12. Contenido real de contacto y textos elegidos

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

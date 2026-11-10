# TAREAS.md

# Plan de trabajo de Neifit

## Roles con permisos específicos

- [x] Centralizar permisos base por rol y aplicarlos en API, guardas de rutas, sidebar y acciones del mensajero.
- [x] Limitar lectura/actualización de entregas a asignados, permitir solo acciones logísticas autorizadas y retirar importes/pagos/correo de la respuesta de mensajería.
- [x] Proteger creación de cotizaciones con sesión y asociarlas al usuario del servidor.
- [x] Añadir panel de gestión de roles/permisos, bloqueo de cambio de rol propio y límites delegables por rol.
- [x] Preparar migración RBAC con funciones de gestión transaccionales, auditoría y políticas RLS por permiso.
- [x] Verificar 32 pruebas frontend, 23 backend, compilación y navegador con sesiones simuladas.
- [ ] Ejecutar `0003_roles_permisos.sql` y `verificar_roles.sql` en Supabase, activar RBAC_DATABASE_ENABLED y probar cambios reales desde una cuenta administradora.

## Landing pública y módulos con autorización

- [x] Independizar login, registro, recuperación y callback Google del layout con sidebar.
- [x] Limitar la navegación de visitantes a la landing, muestra de productos, contenido institucional y acceso/registro.
- [x] Proteger las rutas comerciales y conservar el destino del producto solicitado después del login; mantener permisos por rol y ocultar módulos no autorizados.
- [x] Exigir autenticación para catálogo, detalle, categorías y seguimiento en FastAPI; limitar seguimiento al propietario, administrador o mensajero asignado.
- [x] Publicar únicamente una muestra de tres productos sin cantidades de inventario mediante endpoints específicos de la landing.
- [x] Preparar migración incremental para retirar lectura anónima directa de products y documentar la matriz de acceso en `PLAN_AUTORIZACION.md`.
- [x] Verificar 31 pruebas frontend, 13 pruebas backend y compilación.
- [x] Comprobar en navegador landing pública, login/registro independientes, bloqueo de navegación directa, ausencia de módulos anónimos y regreso al producto después de un login simulado; vista móvil sin desbordamiento.
- [ ] Aplicar `supabase/migrations/0002_catalogo_autenticado.sql` en Supabase y verificar permisos remotos.

## Cambio de logo solicitado

- [x] Copiar el archivo «Neifit_ Sabores Tropicales Saludables.png» como `frontend/public/logo-neifit-tropical.png` y comprobar que coincide con el original.
- [x] Actualizar las siete referencias de imagen/fav­icon a la nueva versión, conservando los activos anteriores.

## Estructura con sidebar de módulos

- [x] Permitir abrir/cerrar el sidebar con clic en escritorio y móvil, iniciando cerrado y ampliando el contenido cuando se oculta. Verificado en navegador a 1440 y 390 px, incluyendo cierre al navegar.

- [x] Implementar layout compartido con encabezado, sidebar izquierdo, contenido derecho y footer a todo el ancho, incluyendo pantallas de autenticación y paneles.
- [x] Mover los módulos del encabezado al sidebar, con estado activo y opciones según rol; conservar logo, contacto, carrito y cuenta en el header.
- [x] Conectar los módulos administrativos mediante URL y retirar las pestañas horizontales duplicadas.
- [x] Implementar menú desplegable en móvil, cierre al navegar y Escape, etiquetas accesibles y enlace para saltar al contenido.
- [x] Verificar en navegador distribución de escritorio y móvil, imágenes, navegación por categorías y ausencia de desbordamiento horizontal; compilación satisfactoria.
- [x] Comprobar menús de administrador, mensajería y cliente con sesiones simuladas y navegación administrativa por URL, sin acceder a cuentas reales.

Evidencia de distribución: `tmp/sidebar-escritorio.png` y `tmp/sidebar-movil-abierto.png`.

## Acceso con Google

- [x] Verificar 28 pruebas frontend, compilación, botón en vista móvil, destino OAuth y pantalla de cancelación con solicitudes interceptadas; sin acceso a cuentas reales Google.

- [x] Implementar «Continuar con Google» en login/registro con Supabase OAuth y callback `/auth/callback`, verificando el perfil y conservando roles de base de datos.
- [x] Documentar configuración Google Auth Platform, Supabase, callbacks y usuarios de prueba en `ACCESO_GOOGLE.md`.
- [ ] Habilitar proveedor remoto y comprobar acceso real con una cuenta autorizada; Google estaba deshabilitado en la comprobación de configuración pública.

## Recuperación de contraseña

- [x] Diferenciar sesión ausente, rechazo de enlace y fallo de comprobación en pantalla.
- [x] Añadir alternativa de recuperación mediante `token_hash`, verificación explícita por el usuario y limpieza del código de la URL tras verificar; mantener el flujo anterior.
- [x] Preparar `supabase/templates/reset_password.html` y probar ambos flujos con el SDK real y respuestas interceptadas, sin modificar cuentas ni enviar correos reales. 24 pruebas frontend satisfactorias.
- [ ] Copiar la plantilla nueva al panel Supabase y comprobar un correo nuevo desde Neifit; respetar los límites de envío.

- [x] Corregir la comprobación prematura de recuperación: esperar `PASSWORD_RECOVERY` cuando `getSession()` responde primero, capturando el tipo de callback antes de la limpieza de URL. 20 pruebas frontend y compilación satisfactorias.

- [x] Añadir «¿Olvidaste tu contraseña?» al inicio de sesión y el formulario de solicitud por correo.
- [x] Añadir `/restablecer-contrasena` con validación de sesión de recuperación, confirmación de contraseña y estados de enlace inválido/caducado, carga, error y éxito.
- [x] Integrar `resetPasswordForEmail`, evento `PASSWORD_RECOVERY` y `updateUser` sin almacenar contraseñas en el proyecto ni simular correos.
- [x] Documentar SMTP, destinos permitidos, plantilla y prueba completa en `RECUPERACION_CONTRASENA.md`.
- [x] Ejecutar 17 pruebas frontend y compilación, satisfactorias.
- [x] Verificar en navegador el enlace desde login, solicitud, destino correcto, error por límite, enlace caducado, confirmación de contraseña, actualización y vista móvil utilizando Supabase simulado; sin envío real ni cambios de contraseñas reales.
- [ ] Configurar SMTP/Redirect URLs en Supabase y probar entrega y recuperación con una cuenta real.

## Revisión de imágenes del proyecto

- [x] Auditar las 12 URL externas restantes: tres devolvían 404 y varias mostraban alimentos distintos al producto.
- [x] Sustituir las imágenes del catálogo y categorías por archivos locales coherentes con el alimento, tanto en backend como en datos demo del frontend.
- [x] Crear `CatalogImage` y un respaldo SVG existente, evitando bucles si falla una imagen; aplicarlo en catálogo, categorías, detalle, carrito, cotizador y administración.
- [x] Resolver las URL antiguas del carrito hacia las nuevas imágenes locales, conservando las fotografías personalizadas.
- [x] Identificar las imágenes generadas como ilustrativas en las tarjetas, categorías y detalle.
- [x] Probar en navegador de escritorio y móvil la carga de imágenes de catálogo, inicio, detalle, carrito, cotizador y login, y simular una imagen rota para comprobar el respaldo sin reintentos infinitos.
- [x] Ejecutar 9 pruebas frontend y compilación, ambas satisfactorias.
- [ ] Sustituir las ilustraciones por fotografías reales aprobadas del negocio y fotografías oficiales de las referencias Fuxion.

Evidencia visual local: `tmp/image-audit/catalogo-escritorio.png`, `snacks-movil.png`, `inicio.png` y `respaldo.png`. La comprobación de navegador verificó 13 imágenes de producto y los logos del catálogo; en móvil no se observó desbordamiento horizontal. Las rutas comerciales de la API aún usan datos demo; esta corrección no implica persistencia de imágenes en Supabase Storage.

## Corrección de imagen de maracuyá

- [x] Sustituir la URL que mostraba un gato por `/images/postre-maracuya.png` en el producto y categoría Postres, tanto en backend como en datos demo del frontend.

La nueva imagen es una ilustración fotorealista generada con imagegen, guardada en `frontend/public/images/postre-maracuya.png`; no representa una fotografía verificada del producto real del negocio.

## Incorporación de logo

- [x] Crear e integrar la versión PNG transparente del logo realista y eliminar el fondo blanco aplicado por CSS en navegación, conservando el archivo original.

- [x] Copiar el PNG suministrado por el usuario a `frontend/public/logo-neifit.png`, conservando sus bytes originales.
- [x] Sustituir el logo provisional en navegación, portada, footer, inicio de sesión y favicon; ajustar tamaños y conservar colores originales.
- [ ] Validar visualmente la composición en navegador móvil y escritorio.

## Entrega Supabase — 7 de noviembre de 2026

- [x] Preparar instalación SQL transaccional con 14 tablas, perfiles automáticos, RLS, Storage y contenido confirmado (archivo generado; pendiente ejecutar en Supabase).
- [x] Preparar SQL de verificación de permisos y guía `CONEXION_SUPABASE.md`.
- [x] Corregir propagación del JWT de Supabase en frontend, actualización del perfil de sesión y confirmación de correo; deshabilitar accesos demo al configurar Supabase.
- [x] Evitar respaldos locales tras fallos de API cuando Supabase está configurado.
- [x] Añadir endpoint autenticado `/api/v1/auth/me` para comprobar JWT y perfil.
- [ ] Ejecutar instalación y verificaciones SQL en la instancia real.
- [ ] Completar credenciales y comprobar registro, confirmación, login y perfil contra Supabase real.
- [ ] Conectar los servicios comerciales a las tablas; mantener pendientes las casillas funcionales que aún usan memoria.

Verificación local: sintaxis de ambos SQL analizada con pglast; 10 pruebas de backend y 5 de frontend aprobadas; compilación frontend correcta. Sin validación remota de SQL, RLS ni autenticación real.

## Avance revisado — 1 de noviembre de 2026

El código existente incluye frontend React/Vite y API FastAPI con módulos de demostración. Las casillas originales se conservan pendientes hasta verificar sus criterios de aceptación; no confundir pantallas implementadas con funcionalidad integrada y validada.

- [x] Revisar documentación y contrastar con la estructura existente.
- [ ] Verificar corrección de autenticación: demo explícito solo en desarrollo, JWT y rol consultado en `profiles` (código y pruebas añadidos).
- [x] Ejecutar pruebas de permisos con dependencias instaladas y Python compatible.
- [ ] Crear/aplicar migraciones Supabase y políticas que impidan la autoasignación de roles.
- [ ] Sustituir memoria de backend por persistencia real y transacciones de inventario.
- [ ] Evitar que los respaldos locales del frontend simulen éxito tras errores de autorización o pagos.
- [ ] Integrar contenido institucional administrable en todas las secciones públicas.
- [ ] Sustituir logo preliminar por activo realista aprobado y validar contenido comercial/legal.

Verificación de esta revisión: `python -m compileall -q backend/app backend/tests` pasó. `unittest` no pudo iniciar por falta de `httpx`; se intentó instalar `backend/requirements.txt`, pero la compilación de `pydantic-core==2.23.4` en Python 3.14 falló por ausencia de `link.exe`. Las pruebas funcionales quedan pendientes de un entorno compatible (Python 3.12 recomendado). No se validó conexión real a Supabase ni despliegue.

## Fase 1. Documentación

Inicialización local posterior: Python 3.12.12 instalado en `.python/`, entorno `backend/.venv/` con dependencias instaladas; 8 pruebas de permisos aprobadas y `npm run build` correcto. Se añadieron scripts PowerShell para arrancar frontend y backend en localhost. La comprobación anterior bloqueada por Python 3.14 queda resuelta para las pruebas automatizadas; integración Supabase y despliegue continúan pendientes.

- [x] Definir nombre del proyecto.
- [x] Definir alcance general.
- [x] Definir módulos principales.
- [x] Definir actores y roles.
- [x] Definir identidad visual base.
- [x] Actualizar documentación con nuevo concepto de logo y colores.

## Fase 2. Diseño

- [ ] Diseñar logo final con ramillete de frutas.
- [ ] Diseñar página de inicio.
- [ ] Diseñar catálogo de productos.
- [ ] Diseñar detalle de producto.
- [ ] Diseñar carro de compras.
- [ ] Diseñar vista de cotizador.
- [ ] Diseñar seguimiento de pedido.
- [ ] Diseñar panel administrador.
- [ ] Diseñar panel de mensajería.
- [ ] Ajustar responsive móvil y escritorio.

## Fase 3. Configuración técnica

- [ ] Crear proyecto React + Vite.
- [ ] Configurar estructura de carpetas.
- [ ] Configurar React Router.
- [ ] Configurar variables de entorno.
- [ ] Conectar Supabase.
- [ ] Definir helpers y servicios.

## Fase 4. Base de datos

- [ ] Crear tabla de perfiles.
- [ ] Crear tabla de categorías.
- [ ] Crear tabla de productos.
- [ ] Crear tablas de carrito.
- [ ] Crear tablas de pedidos.
- [ ] Crear tablas de cotización.
- [ ] Crear tabla de trazabilidad.
- [ ] Crear tabla de transacciones de pago.
- [ ] Implementar políticas RLS.

## Fase 5. Desarrollo funcional

- [ ] Implementar catálogo.
- [ ] Implementar filtros y búsqueda.
- [ ] Implementar detalle de producto.
- [ ] Implementar carrito de compras.
- [ ] Implementar autenticación.
- [ ] Implementar roles.
- [ ] Implementar inventario y disponibilidad.
- [ ] Implementar cotizador.
- [ ] Implementar generación de pedido.
- [ ] Implementar trazabilidad.
- [ ] Implementar panel de mensajería.
- [ ] Implementar panel administrativo.
- [ ] Implementar botón de WhatsApp.
- [ ] Integrar pasarela de pagos.

## Fase 6. Pruebas

- [ ] Probar flujo de registro.
- [ ] Probar flujo de compra.
- [ ] Probar flujo de cotización.
- [ ] Probar actualización de inventario.
- [ ] Probar asignación a mensajería.
- [ ] Probar estados de trazabilidad.
- [ ] Probar permisos por rol.
- [ ] Probar responsive.

## Fase 7. Entrega

- [ ] Preparar README final.
- [ ] Validar documentación.
- [ ] Consolidar scripts SQL.
- [ ] Entregar versión MVP.


## Fase 8. Landing page institucional (nuevo alcance)

- [ ] Crear estructura de frontend React + Vite + Tailwind CSS.
- [ ] Crear estructura del backend Python + FastAPI.
- [ ] Definir contrato API `/api/v1` y validación de JWT de Supabase.
- [ ] Crear sección Hero con logo de frutas realistas aprobado.
- [ ] Crear sección «Quiénes somos».
- [ ] Crear sección «Misión y visión».
- [ ] Crear sección «Nuestros valores».
- [ ] Mostrar categorías destacadas y botones al catálogo.
- [ ] Crear sección Ubicación, Teléfono, WhatsApp y horarios con datos verificados.
- [ ] Crear footer con enlaces y textos legales aprobados.
- [ ] Crear migraciones de contenido institucional y configuración pública.
- [ ] Integrar contenido editable para el administrador.
- [ ] Probar acceso público y permisos de edición.
- [ ] Probar responsividad y accesibilidad de la landing.
- [ ] Validar que las descripciones de Fuxion no incluyan afirmaciones médicas no autorizadas.
- [ ] Registrar resultados de compilación, pruebas de backend y despliegue.

**Datos ya confirmados:** ciudad, dirección, teléfono, enlace de WhatsApp, horario de lunes a viernes y selección de textos corporativos iniciales. **Dependencias abiertas:** proveedor de pagos, coordenadas o enlace de mapa validado, material fotográfico final y aprobación legal de políticas.


## Fase 9. Contenido comercial confirmado

- [x] Registrar ciudad y dirección proporcionadas por el negocio.
- [x] Registrar teléfono y enlace de WhatsApp.
- [x] Registrar horario de lunes a viernes.
- [x] Seleccionar copy institucional propuesto para la primera versión.
- [ ] Implementar estos datos en la landing y en la configuración de Supabase.
- [ ] Verificar visualmente dirección, botón WhatsApp, misión, visión y valores en la aplicación.
- [x] Evitar desmontar el módulo activo al renovar la sesión de la misma cuenta: permisos revalidados en segundo plano; cambio de cuenta y cierre de sesión mantienen bloqueo. Verificado en navegador con respuesta de permisos retenida, 35 pruebas frontend y compilación.

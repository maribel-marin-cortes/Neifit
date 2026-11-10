# Datos de prueba para consultas

Por autorización del usuario se cargaron valores inventados para practicar consultas en el proyecto Supabase conectado. No son precios, inventario, clientes, ventas ni solicitudes comerciales reales.

- 13 productos con nombres sin prefijo, slug `prueba-...`, descripciones breves e imágenes ilustrativas locales. Por solicitud del usuario se retiraron las etiquetas públicas; los precios y existencias siguen siendo valores inventados autorizados. La procedencia se conserva en este documento, en el manifiesto de UUID y en los metadatos privados de las transacciones simuladas.
- 3 cotizaciones: dos pendientes y una respondida.
- 3 pedidos: dos recibidos y uno en preparación; dos escenarios de pago aprobado y uno pendiente. Las aprobaciones son exclusivamente simuladas, sin cobros ni webhooks reales.
- Dos pedidos tienen al administrador como responsable de la simulación, sin crear cuentas ni cambiar roles.
- Los nombres, teléfonos y direcciones de los documentos son inventados y tienen formato habitual; los correos usan `example.com`. No se envían correos, WhatsApp ni notificaciones. Los perfiles reales no se renombran ni se alteran.

Los documentos están asociados a la cuenta administradora autorizada. Otros clientes no ven sus pedidos; pueden crear sus propias solicitudes seleccionando los productos de prueba.

## Consultar

Abre **consultas_datos_prueba.sql** y ejecuta cada consulta por separado en SQL Editor (selecciona su texto y pulsa Run). Si ejecutas todo el archivo, la interfaz puede mostrar únicamente el último resultado. La consulta de pagos aprobados utiliza los dos escenarios simulados.

Para ver el catálogo desde la aplicación, recarga la página. En administración se pueden consultar los pedidos y cotizaciones persistidos. Los números definitivos y UUID están en **datos_consulta_creados.json**.

La creación de los pedidos descontó stock de verdad dentro de este conjunto de prueba; por eso el inventario actual puede ser menor que el inicial del script. No repongas automáticamente esas existencias al repetir una carga.

## Repetir sin duplicados

Desde la raíz, la previsualización no modifica Supabase:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/cargar_datos_consulta.py
```

Para repetir la misma carga autorizada, indica tu cuenta administradora:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/cargar_datos_consulta.py --aplicar --administrador TU_CORREO_ADMIN
```

El script conserva productos existentes de su conjunto sin restablecer precio ni stock, y utiliza identificadores estables para los documentos. No toca productos fuera de esos slugs y no cambia permisos. Si el contenido de un documento ya guardado cambió, puede rechazar la repetición antes que duplicarlo.

## Formato para presentar las consultas

`backend/scripts/presentar_datos_consulta.py` actualiza únicamente los seis documentos del manifiesto y valida sus identificadores deterministas antes de escribir. Retira etiquetas de sus nombres históricos y mensajes, y presenta nombres, direcciones y observaciones habituales. En dos pedidos introduce escenarios de aprobación identificados como `simulacion_consultas` en la tabla privada `payment_transactions`, con `raw_response.simulated=true` y `raw_response.real_funds=false`.

No se comunica con pasarelas ni cambia el comportamiento de aprobación de los pedidos reales de la aplicación. La carga inicial y este formateador son operaciones distintas; la carga inicial continúa creando pagos pendientes.

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/presentar_datos_consulta.py --aplicar --administrador TU_CORREO_ADMIN
```

## Antes de uso comercial

Desactiva los productos de demostración desde Administración y registra productos reales con precio, existencias, ingredientes y alérgenos confirmados. Conserva la procedencia interna de este conjunto y exclúyelo de reportes comerciales reales. Las aprobaciones simuladas no acreditan ingresos ni sustituyen la validación del proveedor para operaciones reales.

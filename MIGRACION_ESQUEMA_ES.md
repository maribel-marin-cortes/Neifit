# Migración técnica al español

## Instalación desde cero

Si se elimina previamente el esquema `public`, el archivo que debe ejecutarse como instalación completa es `supabase/neifit_esquema_completo_espanol.sql`. Este instalador crea tablas físicas y atributos en español; no contiene ninguna instrucción para borrar el esquema y se detiene si detecta tablas de Neifit existentes.

No debe combinarse con `neifit_completo_base_nueva.sql`, `activar_servicios_supabase.sql` ni las migraciones 0002–0009, porque sus cambios ya están incorporados en el instalador completo.

La migración se realiza sin renombrar ni eliminar inmediatamente las tablas que usa producción. La primera etapa crea una API de base de datos completamente en español mediante vistas actualizables y funciones RPC de compatibilidad. Así, los datos, relaciones, restricciones, índices, políticas RLS y disparadores existentes siguen funcionando mientras backend y frontend cambian de contrato.

## Etapa 1: compatibilidad sin interrupción

1. Hacer una copia de seguridad de la base de datos.
2. Ejecutar `supabase/migrations/0009_capa_compatibilidad_espanol.sql` completo en el SQL Editor de Supabase.
3. Desplegar el backend actualizado.
4. Desplegar el frontend actualizado.
5. Validar acceso con Google, perfil, direcciones, catálogo, pedidos, cotizaciones, mensajería, notificaciones y administración.

La migración 0009 crea nombres españoles como `perfiles`, `productos`, `pedidos`, `cotizaciones`, `direcciones_cliente` y `notificaciones`. También publica RPC como `neifit_leer_pedidos`, `neifit_actualizar_pedido`, `neifit_asignar_mensajero` y `neifit_asignar_rol`.

Las rutas principales de la API quedan en español (`/productos`, `/pedidos`, `/cotizaciones`, `/seguimiento`, `/cuenta`, `/accesos`). Las rutas inglesas permanecen temporalmente como alias obsoletos para permitir una actualización gradual.

## Etapa 2: contrato de datos

Durante la transición, el backend conserva las claves JSON inglesas que ya consume React. Esta decisión evita mezclar una migración estructural con una modificación simultánea de todos los componentes visuales y permite revertir el despliegue sin pérdida de datos.

Una vez que producción haya funcionado correctamente con 0009, se traducirán los modelos de entrada/salida y las claves JSON. Esa etapa debe publicarse conjuntamente en backend y frontend.

## Etapa 3: renombrado físico

El renombrado físico de tablas y columnas solo debe realizarse cuando no existan consumidores de los nombres antiguos. En esa etapa se crean alias ingleses temporales, se vuelven a generar las políticas y dependencias, se valida el catálogo de PostgreSQL y finalmente se retiran los alias.

No se debe renombrar directamente el esquema actual antes de desplegar 0009: el inicio con Google consulta el perfil desde el navegador y una actualización parcial bloquearía el acceso de usuarios.

## Reversión de la primera etapa

La etapa 1 no mueve ni transforma registros. Si el despliegue presenta un problema, se puede volver a la versión anterior del backend/frontend; las tablas inglesas originales continúan intactas. Las vistas y RPC españolas pueden mantenerse porque no modifican el almacenamiento físico.

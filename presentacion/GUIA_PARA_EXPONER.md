# Neifit · Lista para presentar

Fecha: 10 de noviembre de 2026. Duración sugerida: 12–15 minutos (incluye cinco consultas SQL).

## Presentación animada

Abre Neifit_presentacion_animada.html con doble clic en Chrome o Edge. Funciona sin conexión, sin iniciar el proyecto y sin instalar nada.

- Flechas o espacio: avanzar y retroceder.
- F: pantalla completa.
- N: mostrar u ocultar el guion. Se ve en la misma pantalla: ocúltalo antes de proyectar si no quieres que el público lo vea.
- O: índice para saltar a una diapositiva.
- Inicio / Fin: primera o última diapositiva.
- Esc: cerrar guion o índice. El navegador también usa Esc para salir de pantalla completa.
- Ctrl + P: imprimir o guardar en PDF. Las animaciones se convierten en páginas estáticas.

La presentación HTML incluye sus recursos. No necesitas conexión a Canva, Google Fonts ni ningún CDN.

## Editar o importar en Canva

Abre Neifit_presentacion_consultas.pptx con PowerPoint, o entra a Canva y utiliza su opción de importar/subir archivo para cargar el PPTX. Los textos, tablas y diagramas se construyeron como elementos editables. Revisa tipografía y distribución después de importar. Las transiciones de PowerPoint pueden no conservarse en Canva: aplica allí las animaciones que prefieras. La versión HTML ya incluye animaciones.

No se creó ni publicó una presentación dentro de una cuenta de Canva. Este paquete contiene los archivos para usar o importar.

## Respaldo

Neifit_presentacion_consultas.pdf es la versión fija para exponer si no puedes utilizar el HTML o PowerPoint. El PDF no tiene animaciones.

## Antes de exponer

1. Abre el HTML y prueba las flechas, pantalla completa y guion.
2. Conserva el PDF y el PPTX como respaldo.
3. Si harás una demostración del sistema, inicia backend y frontend por separado. El HTML de la presentación no los necesita.
4. No proyectes .env, claves ni enlaces con tokens.
5. Explica que pedidos y cotizaciones siguen en memoria; no prometas persistencia ni pagos terminados.

## Guion por diapositiva

### 1. Neifit

Buenos días. Somos Maribel Marín Cortés, Nixon Garcia y Flor Neifix González, y presentamos Neifit: una tienda virtual para organizar la oferta de postres, snacks y bebidas. El proyecto conecta la experiencia de compra del cliente con la gestión administrativa y el seguimiento de entregas. Vamos a explicar la necesidad, los usuarios, el modelo de datos y el estado actual del desarrollo.

### 2. Una venta necesita más que un mensaje.

La necesidad es organizar el proceso comercial en un solo sistema. Cuando las solicitudes se manejan de forma dispersa, puede ser difícil identificar qué pidió cada cliente, qué solicitudes están pendientes y cómo avanza una entrega. Estos son los problemas que el proyecto busca solucionar; no son resultados de una encuesta ni estadísticas medidas de la empresa.

### 3. De conocer la marca a recibir el pedido.

El recorrido empieza en una página pública donde el visitante conoce la empresa. Para acceder a los módulos comerciales se requiere iniciar sesión. El cliente puede comprar o cotizar; el administrador consulta las solicitudes; y el mensajero gestiona sus entregas asignadas. React y Vite construyen la interfaz, FastAPI aplica las reglas y Supabase aporta autenticación y la base de datos diseñada. La integración persistente de pedidos y cotizaciones todavía está pendiente.

### 4. Una plataforma. Responsabilidades distintas.

Los actores principales son el cliente, el administrador y el mensajero. Cada uno necesita información diferente. Un cliente no debe ver pedidos ajenos y un mensajero no debe administrar usuarios. La ampliación de roles personalizados permite autorizar funciones como inventario sin otorgar toda la administración. Esta gestión requiere las migraciones y la configuración descritas en el proyecto.

### 5. ¿Qué necesita conocer el sistema?

El sistema maneja información de personas, productos, operaciones y control. También contempla el contenido institucional, como misión, valores y datos de contacto. Una decisión importante es no guardar contraseñas en la tabla de perfiles: la autenticación corresponde a Supabase Auth. La tabla de perfiles conserva la información necesaria para la operación y la autorización.

### 6. La base del modelo.

La tabla profiles se vincula con auth.users. Las categorías agrupan los productos, y cada producto pertenece a una categoría. El producto incluye precio y stock, además de información descriptiva. El carrito se separa de sus detalles para que pueda contener varios productos sin repetir todos los datos del usuario. Los atributos mostrados son un resumen del SQL, no la lista completa de columnas.

### 7. Cada solicitud conserva su detalle.

Los pedidos y las cotizaciones son entidades diferentes porque representan momentos distintos del proceso comercial. Sus detalles resuelven la relación con los productos. El detalle de un pedido conserva el nombre y el precio de la compra aunque el catálogo cambie después. El seguimiento conserva eventos en el tiempo. Las transacciones de pago están contempladas en el esquema, pero no se presenta una pasarela real como terminada.

### 8. Las relaciones dan coherencia al negocio.

Un usuario puede tener muchos pedidos y cotizaciones. Un pedido tiene muchos detalles; cada detalle referencia un producto. De manera similar, una cotización contiene varios detalles. Una categoría tiene muchos productos. El pedido también puede tener muchos eventos de seguimiento y transacciones de pago. La asignación del mensajero es otra relación con profiles, distinta del cliente que hizo la compra. El diagrama resume las relaciones principales y no todas las tablas del esquema.

### 9. El acceso depende de lo autorizado.

Los usuarios tienen un rol y los permisos se asignan al rol. access_roles define los roles; permissions identifica las acciones; y role_permissions relaciona ambos. También se incluyen límites delegables y auditoría de cambios. Ocultar una opción del menú mejora la experiencia, pero no garantiza seguridad: FastAPI valida permisos y propiedad en cada operación. La gestión de usuarios y de roles está reservada al administrador.

### 10. Reglas que protegen la información.

Las restricciones evitan valores imposibles, duplicaciones y referencias inexistentes. Las claves foráneas conectan las tablas; los valores únicos identifican documentos; y las restricciones check limitan estados y cantidades. También se consideran reglas de autorización y RLS. La validación transaccional de stock y totales desde el servidor debe completarse junto con la persistencia comercial; no basta con comprobar que un valor sea positivo.

### 11. Un modelo relacional para crecer con orden.

El modelo relacional se ajusta a un negocio con relaciones claras y necesidad de consistencia. Separar los detalles de las cabeceras facilita manejar varios productos por solicitud. Guardar ciertos datos históricos en el pedido es una duplicación deliberada: permite conservar el contexto de la compra. Además, separar transacciones de pago admite varios intentos para un mismo pedido. El diseño busca crecer sin mezclar las responsabilidades de cada entidad.

### 12. Productos con pocas unidades

Identificar productos activos con cinco unidades o menos. Permite priorizar la revisión del inventario. Incluye productos agotados. Esta consulta utiliza SQL de PostgreSQL. Los resultados dependen de los datos realmente guardados en la base de datos; no recupera registros que solo existían en memoria.

### 13. Cotizaciones pendientes

Consultar las solicitudes sin responder y su importe de referencia. El importe suma cantidad × precio de referencia; no incluye domicilio ni es un pago confirmado. Esta consulta utiliza SQL de PostgreSQL. Los resultados dependen de los datos realmente guardados en la base de datos; no recupera registros que solo existían en memoria.

### 14. Entregas por mensajero

Consultar pedidos asignados que aún no están entregados ni cancelados. Muestra responsable, cliente, dirección y estado. El JOIN excluye pedidos sin mensajero asignado. Esta consulta utiliza SQL de PostgreSQL. Los resultados dependen de los datos realmente guardados en la base de datos; no recupera registros que solo existían en memoria.

### 15. Productos con más unidades vendidas

Sumar unidades e importes de pedidos no cancelados con pago aprobado. Agrupa por producto. El importe corresponde a sus detalles, sin sumar el domicilio. Esta consulta utiliza SQL de PostgreSQL. Los resultados dependen de los datos realmente guardados en la base de datos; no recupera registros que solo existían en memoria.

### 16. Usuarios y sus roles

Relacionar las cuentas registradas con el nombre de su rol. Permite revisar asignaciones. Requiere la tabla access_roles y una cuenta autorizada. Esta consulta utiliza SQL de PostgreSQL. Los resultados dependen de los datos realmente guardados en la base de datos; no recupera registros que solo existían en memoria.

### 17. Prototipo funcional, con una ruta de evolución.

Es importante explicar el estado real. Existe una interfaz funcional y controles de acceso, así como un esquema SQL para la base de datos. La gestión persistente de roles requiere aplicar sus migraciones y activar la configuración; no se asegura aquí que estén instaladas en la instancia. Los servicios comerciales de pedidos y cotizaciones todavía almacenan datos en memoria. La siguiente prioridad es la persistencia transaccional, seguida por pagos reales y validación completa de la operación.

### 18. Organizar la venta. Acompañar cada entrega.

Para cerrar, Neifit propone una experiencia de compra cercana y una operación más organizada. En una demostración puedo recorrer la landing, el catálogo y la solicitud de cotización, y después mostrar el panel administrativo con una cuenta autorizada. Debo mantener el backend encendido y no prometer que los datos sobreviven a un reinicio. Los siguientes pasos son consolidar persistencia y transacciones, integrar pagos y validar la operación completa. Muchas gracias. Quedo atenta a sus preguntas.


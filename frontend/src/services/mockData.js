export const initialCompanySettings = {
  business_name: "Neifit",
  phone_public: "+57 3127827020",
  whatsapp_number: "573127827020",
  whatsapp_url: "https://wa.me/573127827020",
  address: "CR 28B # 38F - 56",
  city: "Medellín, Antioquia, Colombia",
  opening_hours: {
    weekdays: "Lunes a viernes: 9:00 a. m. a 6:00 p. m. (hora Colombia)",
    weekends: "Fines de semana y festivos: No disponible"
  },
  map_search_url: "https://www.google.com/maps/search/?api=1&query=CR+28B+%23+38F+-+56%2C+Medell%C3%ADn%2C+Colombia"
};

export const initialSiteContent = {
  hero_title: "Sabores naturales que cuentan historias",
  hero_description: "Postres artesanales, snacks nutritivos y bebidas seleccionadas con el sabor de nuestras raíces colombianas. Frescura, tradición y salud en cada bocado.",
  about_us: "En Neifit reunimos sabores tradicionales, frutas y opciones para acompañar distintos momentos del día. Queremos que comprar sea una experiencia cercana y sencilla.",
  mission: "Ofrecer una selección de postres, snacks y bebidas con atención cálida, información transparente y respeto por los sabores regionales.",
  vision: "Ser una marca colombiana reconocida por conectar tradición, variedad y una experiencia de compra confiable."
};

export const initialCompanyValues = [
  {
    id: "val-1",
    title: "Calidad",
    description: "Cuidamos rigurosamente la frescura de nuestras frutas y la selección de cada insumo natural.",
    sort_order: 1
  },
  {
    id: "val-2",
    title: "Transparencia",
    description: "Compartimos ingredientes, porciones y valores claros sin falsas promesas nutricionales.",
    sort_order: 2
  },
  {
    id: "val-3",
    title: "Cercanía",
    description: "Brindamos atención personalizada directa por WhatsApp y soporte continuo en cada pedido.",
    sort_order: 3
  },
  {
    id: "val-4",
    title: "Innovación",
    description: "Reinventamos recetas clásicas colombianas en versiones equilibradas y saludables.",
    sort_order: 4
  },
  {
    id: "val-5",
    title: "Responsabilidad",
    description: "Compromiso con buenas prácticas higiénicas, empaques amigables y trazabilidad logística.",
    sort_order: 5
  },
  {
    id: "val-6",
    title: "Tradición",
    description: "Celebramos el patrimonio gastronómico de nuestras regiones: maracuyá, mango, coco y chontaduro.",
    sort_order: 6
  }
];

export const initialCategories = [
  {
    id: "cat-1",
    name: "Postres",
    slug: "postres",
    description: "Postres saludables elaborados con frutas naturales e inspiración regional.",
    image: "/images/postre-maracuya.png"
  },
  {
    id: "cat-2",
    name: "Snacks",
    slug: "snacks",
    description: "Bocados prácticos, dátiles, cocadas artesanales y frutos secos para cualquier momento.",
    image: "/images/cocadas.png"
  },
  {
    id: "cat-3",
    name: "Bebidas",
    slug: "bebidas",
    description: "Bebidas nutracéuticas Fuxion para complementar tu hidratación y bienestar activo.",
    image: "/images/bebidas-ilustrativas.png"
  }
];

export const initialProducts = [
  // Postres
  {
    id: "prod-1",
    category_id: "cat-1",
    category_slug: "postres",
    category_name: "Postres",
    name: "Postre de Maracuyá Saludable",
    slug: "postre-de-maracuya-saludable",
    description: "Esponjosa crema ligera de maracuyá colombiano con reducción natural de pulpa ácida, endulzado sutilmente sin azúcar refinada.",
    price: 12500,
    stock: 24,
    is_available: true,
    featured: true,
    image_url: "/images/postre-maracuya.png"
  },
  {
    id: "prod-2",
    category_id: "cat-1",
    category_slug: "postres",
    category_name: "Postres",
    name: "Mousse Natural de Mango",
    slug: "mousse-natural-de-mango",
    description: "Cremoso postre a base de pulpa fresca de mango Tommy maduro con toque de chía y base de avena tostada.",
    price: 13000,
    stock: 18,
    is_available: true,
    featured: true,
    image_url: "/images/mousse-mango.png"
  },
  {
    id: "prod-3",
    category_id: "cat-1",
    category_slug: "postres",
    category_name: "Postres",
    name: "Delicia de Fresa y Frutos Rojos",
    slug: "delicia-de-fresa-y-frutos-rojos",
    description: "Fresas frescas seleccionadas en coulis aromático con crema de coco ligera y crumble artesanal.",
    price: 13500,
    stock: 15,
    is_available: true,
    featured: false,
    image_url: "/images/postre-fresa.png"
  },
  {
    id: "prod-4",
    category_id: "cat-1",
    category_slug: "postres",
    category_name: "Postres",
    name: "Postre de Melocotón Dorado",
    slug: "postre-de-melocoton-dorado",
    description: "Capas de melocotón en láminas suaves, yogur griego natural y especias aromáticas de canela y cardamomo.",
    price: 12800,
    stock: 12,
    is_available: true,
    featured: false,
    image_url: "/images/postre-melocoton.png"
  },
  {
    id: "prod-5",
    category_id: "cat-1",
    category_slug: "postres",
    category_name: "Postres",
    name: "Torta Húmeda de Chontaduro",
    slug: "torta-humeda-de-chontaduro",
    description: "Homenaje al Pacífico colombiano: masa suave con pulpa auténtica de chontaduro, coco y toque de miel cruda.",
    price: 14500,
    stock: 10,
    is_available: true,
    featured: true,
    image_url: "/images/torta-chontaduro.png"
  },
  {
    id: "prod-6",
    category_id: "cat-1",
    category_slug: "postres",
    category_name: "Postres",
    name: "Postre Tradicional Regional Reinterpretado",
    slug: "postre-tradicional-regional",
    description: "Inspirado en los sabores andinos de arequipe de leche de almendras y queso campesino bajo en sodio.",
    price: 14000,
    stock: 0,
    is_available: false,
    featured: false,
    image_url: "/images/postre-regional.png"
  },

  // Snacks
  {
    id: "prod-7",
    category_id: "cat-2",
    category_slug: "snacks",
    category_name: "Snacks",
    name: "Cocadas Artesanales sin Azúcar",
    slug: "cocadas-artesanales-sin-azucar",
    description: "Coco rallado tostado con panela orgánica de caña y clavo dulce. Textura masticable tradicional.",
    price: 8500,
    stock: 30,
    is_available: true,
    featured: true,
    image_url: "/images/cocadas.png"
  },
  {
    id: "prod-8",
    category_id: "cat-2",
    category_slug: "snacks",
    category_name: "Snacks",
    name: "Dátiles Medjool con Crema de Maní",
    slug: "datiles-rellenos-crema-mani",
    description: "Dátiles carnosos rellenos de mantequilla de maní 100% natural, cubiertos con nibs de cacao puro.",
    price: 11000,
    stock: 22,
    is_available: true,
    featured: true,
    image_url: "/images/datiles-mani.png"
  },
  {
    id: "prod-9",
    category_id: "cat-2",
    category_slug: "snacks",
    category_name: "Snacks",
    name: "Maní Tostado Natural al Horno",
    slug: "mani-tostado-natural",
    description: "Maní tostado lentamente con sal rosada de montaña y especias naturales. Sin aceites añadidos.",
    price: 6000,
    stock: 45,
    is_available: true,
    featured: false,
    image_url: "/images/mani-tostado.png"
  },
  {
    id: "prod-10",
    category_id: "cat-2",
    category_slug: "snacks",
    category_name: "Snacks",
    name: "Mix de Frutos Secos y Semillas",
    slug: "mix-frutos-secos-semillas",
    description: "Mezcla de almendras enteras, nueces del nogal, semillas de calabaza y arándanos deshidratados.",
    price: 12000,
    stock: 25,
    is_available: true,
    featured: false,
    image_url: "/images/mix-frutos-secos.png"
  },

  // Bebidas
  {
    id: "prod-11",
    category_id: "cat-3",
    category_slug: "bebidas",
    category_name: "Bebidas",
    name: "Bebida Fuxion Prunex 1",
    slug: "fuxion-prunex-1",
    description: "Té herbal nutracéutico con sabor a ciruela y extracto de linaza para el bienestar digestivo regular.",
    price: 22000,
    stock: 14,
    is_available: true,
    featured: true,
    image_url: "/images/bebidas-ilustrativas.png"
  },
  {
    id: "prod-12",
    category_id: "cat-3",
    category_slug: "bebidas",
    category_name: "Bebidas",
    name: "Bebida Fuxion Flora Liv",
    slug: "fuxion-flora-liv",
    description: "Deliciosa bebida sabor a granadilla con cultivo probiótico y fibra prebiótica para el equilibrio intestinal.",
    price: 24000,
    stock: 16,
    is_available: true,
    featured: true,
    image_url: "/images/bebidas-ilustrativas.png"
  },
  {
    id: "prod-13",
    category_id: "cat-3",
    category_slug: "bebidas",
    category_name: "Bebidas",
    name: "Bebida Fuxion Vita Xtra T+",
    slug: "fuxion-vita-xtra-t",
    description: "Bebida antioxidante con extractos de maíz morado, camu camu, maca y ginseng para energía natural.",
    price: 25000,
    stock: 8,
    is_available: true,
    featured: false,
    image_url: "/images/bebidas-ilustrativas.png"
  }
];

export const initialOrders = [
  {
    id: "ord-101",
    order_number: "NF-2026-001",
    user_id: "usr-cliente-1",
    customer_name: "María Fernanda Gómez",
    customer_phone: "+57 300 1234567",
    customer_email: "maria.gomez@gmail.com",
    address: "Calle 10 # 43E - 22, El Poblado, Medellín",
    order_status: "en_ruta",
    payment_status: "aprobado",
    payment_method: "wompi",
    subtotal: 25500,
    shipping_cost: 5000,
    total: 30500,
    assigned_delivery_user_id: "usr-delivery-1",
    assigned_delivery_name: "Carlos Mensajero Neifit",
    notes: "Entregar en portería torre 2",
    created_at: "2026-11-01T10:30:00Z",
    items: [
      { id: "oi-1", product_name: "Postre de Maracuyá Saludable", quantity: 1, unit_price: 12500, subtotal: 12500 },
      { id: "oi-2", product_name: "Mousse Natural de Mango", quantity: 1, unit_price: 13000, subtotal: 13000 }
    ],
    tracking_history: [
      { status: "recibido", message: "Pedido recibido en el sistema de Neifit.", timestamp: "2026-11-01T10:30:00Z" },
      { status: "confirmado", message: "Pago confirmado exitosamente.", timestamp: "2026-11-01T10:32:00Z" },
      { status: "en_preparacion", message: "Cocina artesanal preparando los postres frescos.", timestamp: "2026-11-01T11:00:00Z" },
      { status: "empacado", message: "Pedido empacado en contenedor isotérmico ecológico.", timestamp: "2026-11-01T11:45:00Z" },
      { status: "en_ruta", message: "Mensajero Carlos en camino a la dirección indicada.", timestamp: "2026-11-01T12:15:00Z" }
    ]
  },
  {
    id: "ord-102",
    order_number: "NF-2026-002",
    user_id: "usr-cliente-2",
    customer_name: "Andrés Felipe Ruiz",
    customer_phone: "+57 311 9876543",
    customer_email: "andres.ruiz@hotmail.com",
    address: "Circular 4 # 73 - 15, Laureles, Medellín",
    order_status: "entregado",
    payment_status: "aprobado",
    payment_method: "transferencia",
    subtotal: 33000,
    shipping_cost: 5000,
    total: 38000,
    assigned_delivery_user_id: "usr-delivery-1",
    assigned_delivery_name: "Carlos Mensajero Neifit",
    notes: "Timbre 301",
    created_at: "2026-10-31T15:20:00Z",
    items: [
      { id: "oi-3", product_name: "Dátiles Medjool con Crema de Maní", quantity: 3, unit_price: 11000, subtotal: 33000 }
    ],
    tracking_history: [
      { status: "recibido", message: "Pedido recibido.", timestamp: "2026-10-31T15:20:00Z" },
      { status: "confirmado", message: "Confirmado.", timestamp: "2026-10-31T15:25:00Z" },
      { status: "despachado", message: "Despachado con mensajería.", timestamp: "2026-10-31T16:00:00Z" },
      { status: "entregado", message: "Entregado a satisfacción al cliente.", timestamp: "2026-10-31T17:10:00Z" }
    ]
  }
];

export const initialQuotes = [
  {
    id: "quot-101",
    quote_number: "COT-2026-001",
    customer_name: "Empresa Salud & Bienestar SAS",
    customer_phone: "+57 315 4443322",
    customer_email: "bienestar@empresa.com",
    status: "pendiente",
    notes: "Cotización para refrigerio corporativo de 40 personas el 15 de noviembre.",
    created_at: "2026-11-01T09:15:00Z",
    items: [
      { product_name: "Cocadas Artesanales sin Azúcar", quantity: 40, reference_price: 8500 },
      { product_name: "Bebida Fuxion Vita Xtra T+", quantity: 40, reference_price: 25000 }
    ]
  }
];


export const PRODUCT_IMAGE_FALLBACK = '/placeholder-product.svg';

// Compatibilidad con imágenes antiguas guardadas en el carrito o datos demo.
const replacements = {
  'photo-1541781774459-bb2af2f05b55': 'postre-maracuya',
  'photo-1563805042-7684c019e1cb': 'mousse-mango',
  'photo-1488477181946-6428a0291777': 'postre-fresa',
  'photo-1551024709-8f23befc6f87': 'postre-melocoton',
  'photo-1578985545062-69928b1d9587': 'torta-chontaduro',
  'photo-1587314168485-3236d6710814': 'postre-regional',
  'photo-1599599810769-bcde5a160d32': 'cocadas',
  'photo-1505253758473-96b46d5f69fe': 'datiles-mani',
  'photo-1569460275917-062e74e6c1e9': 'mani-tostado',
  'photo-1536591375315-1b8384210a48': 'mix-frutos-secos',
  'photo-1513558161293-cdaf765ed2fd': 'bebidas-ilustrativas',
  'photo-1556881286-fc6915169721': 'bebidas-ilustrativas',
  'photo-1546173159-315724a31696': 'bebidas-ilustrativas',
};
const illustrativePaths = new Set(Object.values(replacements).map(name => `/images/${name}.png`));

export function resolveImageSource(value) {
  if (typeof value !== 'string' || !value.trim()) return PRODUCT_IMAGE_FALLBACK;
  const src = value.trim();
  try {
    const url = new URL(src);
    const name = replacements[url.pathname.slice(1)];
    if (url.hostname === 'images.unsplash.com' && name) return `/images/${name}.png`;
  } catch { /* Las rutas locales se conservan. */ }
  return src;
}

export function isIllustrativeImage(src) {
  return illustrativePaths.has(resolveImageSource(src));
}

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { access } from 'node:fs/promises';
import { resolveImageSource, PRODUCT_IMAGE_FALLBACK, isIllustrativeImage } from '../services/catalogImages.js';
import { initialProducts, initialCategories } from '../services/mockData.js';

test('todas las imágenes del catálogo y categorías son archivos locales existentes', async () => {
  for (const image of [...initialProducts.map(p => p.image_url), ...initialCategories.map(c => c.image)]) {
    assert.ok(image.startsWith('/images/'), image);
    await access(new URL(`../../public${image}`, import.meta.url));
    assert.equal(isIllustrativeImage(image), true);
  }
});

test('el carrito antiguo encuentra las nuevas fotos de los snacks con URL rota', () => {
  for (const [id, name] of [
    ['1505253758473-96b46d5f69fe', 'datiles-mani'],
    ['1569460275917-062e74e6c1e9', 'mani-tostado'],
    ['1536591375315-1b8384210a48', 'mix-frutos-secos'],
  ]) {
    assert.equal(resolveImageSource(`https://images.unsplash.com/photo-${id}?w=600`), `/images/${name}.png`);
  }
});

test('los productos sin imagen tienen un respaldo local existente', async () => {
  for (const value of [null, undefined, '', '   ']) assert.equal(resolveImageSource(value), PRODUCT_IMAGE_FALLBACK);
  await access(new URL(`../../public${PRODUCT_IMAGE_FALLBACK}`, import.meta.url));
});

test('las fotos personalizadas y las imágenes de marca se conservan', () => {
  for (const value of ['https://example.com/producto.webp', '/logo-neifit-transparente.png']) {
    assert.equal(resolveImageSource(value), value);
    assert.equal(isIllustrativeImage(value), false);
  }
  assert.equal(resolveImageSource('https://example.com/photo-1505253758473-96b46d5f69fe'),
    'https://example.com/photo-1505253758473-96b46d5f69fe');
});

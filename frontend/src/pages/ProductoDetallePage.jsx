import CatalogImage from '../components/CatalogImage';
import { isIllustrativeImage } from '../services/catalogImages';
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ShoppingBag, MessageCircle, CheckCircle, XCircle, Share2 } from 'lucide-react';
import { api } from '../services/api';
import { useCart } from '../context/CartContext';
import { formatCOP } from '../components/ProductCard';

export default function ProductoDetallePage() {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [qty, setQty] = useState(1);
  const [addedMsg, setAddedMsg] = useState('');
  const { addToCart } = useCart();

  useEffect(() => {
    setLoading(true);
    api.getProductBySlug(slug)
      .then(setProduct)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [slug]);

  const handleAddToCart = () => {
    const success = addToCart(product, qty);
    if (success) {
      setAddedMsg(`✓ ${qty} unidad(es) añadida(s) al carrito`);
      setTimeout(() => setAddedMsg(''), 2500);
    }
  };

  const waText = product
    ? `Hola Neifit! Me interesa el producto: *${product.name}* ($${formatCOP(product.price)}). ¿Está disponible?`
    : '';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-10 h-10 rounded-full border-4 border-[#7A4E2D] border-t-transparent" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center">
        <p className="text-5xl">😕</p>
        <h2 className="font-display font-bold text-2xl text-[#4B2E1F]">Producto no encontrado</h2>
        <p className="text-[#7A4E2D]/70">{error || 'El producto que buscas no existe o fue removido.'}</p>
        <Link to="/catalogo" className="btn-primary">← Volver al catálogo</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-[#7A4E2D]/60 mb-8">
          <Link to="/" className="hover:text-[#7A4E2D]">Inicio</Link>
          <span>/</span>
          <Link to="/catalogo" className="hover:text-[#7A4E2D]">Catálogo</Link>
          <span>/</span>
          <Link to={`/catalogo?cat=${product.category_slug}`} className="hover:text-[#7A4E2D]">{product.category_name}</Link>
          <span>/</span>
          <span className="text-[#4B2E1F] font-medium truncate max-w-[180px]">{product.name}</span>
        </nav>

        <div className="grid md:grid-cols-2 gap-10">
          {/* Image */}
          <div className="relative rounded-2xl overflow-hidden aspect-[4/3] bg-[#FFF8F2]">
            <CatalogImage
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
            {!product.is_available && (
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                <span className="bg-white/90 text-red-700 font-bold px-4 py-2 rounded-full text-sm uppercase tracking-wider">
                  Agotado
                </span>
              </div>
            )}
            {product.featured && (
              <span className="absolute top-3 left-3 badge-pink text-xs font-bold uppercase tracking-wide">Destacado ⭐</span>
            )}
            {isIllustrativeImage(product.image_url) && (
              <span className="absolute bottom-3 right-3 rounded bg-[#FFF8F2]/95 px-2 py-1 text-xs text-[#4B2E1F]">
                Imagen ilustrativa
              </span>
            )}
          </div>

          {/* Info */}
          <div className="flex flex-col gap-4">
            <span className="text-sm font-bold uppercase tracking-widest text-[#5F8D4E]">{product.category_name}</span>
            <h1 className="font-display font-extrabold text-3xl text-[#4B2E1F] leading-snug">{product.name}</h1>
            <p className="text-[#7A4E2D]/80 leading-relaxed">{product.description}</p>

            {/* Stock & Availability */}
            <div className="flex items-center gap-2 py-3 border-y border-[#7A4E2D]/10">
              {product.is_available ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-green-700 font-semibold">Disponible — {product.stock} unidades</span>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-500" />
                  <span className="text-red-600 font-semibold">Agotado temporalmente</span>
                </>
              )}
            </div>

            {/* Price */}
            <div className="text-3xl font-display font-extrabold text-[#7A4E2D]">
              {formatCOP(product.price)}
            </div>

            {/* Quantity & Add to Cart */}
            {product.is_available && (
              <div className="flex items-center gap-3">
                <div className="flex items-center border border-[#7A4E2D]/25 rounded-xl overflow-hidden bg-[#FFF8F2]">
                  <button
                    onClick={() => setQty(q => Math.max(1, q - 1))}
                    className="px-4 py-2.5 text-[#7A4E2D] hover:bg-[#F6E7D8] font-bold transition-colors"
                    aria-label="Disminuir cantidad"
                  >–</button>
                  <span className="px-4 py-2.5 font-bold text-[#4B2E1F] min-w-[3rem] text-center">{qty}</span>
                  <button
                    onClick={() => setQty(q => Math.min(product.stock, q + 1))}
                    className="px-4 py-2.5 text-[#7A4E2D] hover:bg-[#F6E7D8] font-bold transition-colors"
                    aria-label="Aumentar cantidad"
                  >+</button>
                </div>
                <button
                  onClick={handleAddToCart}
                  className="btn-primary flex-1 justify-center py-2.5 text-base"
                >
                  <ShoppingBag className="w-5 h-5" />
                  Agregar al carrito
                </button>
              </div>
            )}

            {addedMsg && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm rounded-xl px-4 py-2.5 font-medium">
                {addedMsg}
              </div>
            )}

            {/* WhatsApp action */}
            <a
              href={`https://wa.me/573127827020?text=${encodeURIComponent(waText)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary justify-center"
            >
              <MessageCircle className="w-4 h-4" />
              Consultar disponibilidad por WhatsApp
            </a>

            <Link to="/cotizador" className="btn-outline justify-center text-sm">
              ¿Necesitas cantidad mayor? Solicitar cotización →
            </Link>
          </div>
        </div>

        <div className="mt-10">
          <Link to="/catalogo" className="inline-flex items-center gap-2 text-[#7A4E2D] hover:underline text-sm font-medium">
            <ArrowLeft className="w-4 h-4" />
            Volver al catálogo
          </Link>
        </div>
      </div>
    </div>
  );
}


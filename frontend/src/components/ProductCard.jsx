import CatalogImage from './CatalogImage';
import { isIllustrativeImage } from '../services/catalogImages';
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginLink } from '../services/accessPolicy';
import { ShoppingBag, Eye, CheckCircle, XCircle } from 'lucide-react';
import { useCart } from '../context/CartContext';

export function formatCOP(amount) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(amount);
}

export default function ProductCard({ product }) {
  const { addToCart } = useCart();
  const { user, hasPermission } = useAuth();
  const navigate = useNavigate();
  const [added, setAdded] = React.useState(false);

  const handleAddToCart = (e) => {
    e.preventDefault();
    if (!user) {
      navigate(loginLink(`/productos/${product.slug}`));
      return;
    }
    if (!hasPermission('orders.create')) { navigate(`/productos/${product.slug}`); return; }
    const success = addToCart(product, 1);
    if (success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 1800);
    }
  };

  return (
    <article className="card-cream flex flex-col group overflow-hidden">
      {/* Product image */}
      <Link to={`/productos/${product.slug}`} className="relative block shrink-0 overflow-hidden aspect-[4/3]">
        <CatalogImage
          src={product.image_url}
          alt={product.name}
          loading="lazy"
          className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        {!product.is_available && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <span className="bg-white/90 text-red-700 font-bold text-xs px-3 py-1.5 rounded-full uppercase tracking-wide">
              Agotado
            </span>
          </div>
        )}
        {product.featured && product.is_available && (
          <span className="absolute top-2 left-2 badge-pink text-[11px] font-bold uppercase tracking-wide">
            Destacado
          </span>
        )}
        {isIllustrativeImage(product.image_url) && (
          <span className="absolute bottom-2 right-2 rounded bg-[#FFF8F2]/95 px-2 py-1 text-[10px] text-[#4B2E1F]">
            Imagen ilustrativa
          </span>
        )}
      </Link>

      {/* Card body */}
      <div className="flex flex-col flex-1 p-4 gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-[#5F8D4E]">
          {product.category_name}
        </span>
        <h3 className="font-display font-semibold text-[#4B2E1F] text-base leading-snug line-clamp-2">
          <Link to={`/productos/${product.slug}`} className="hover:text-[#7A4E2D] transition-colors">
            {product.name}
          </Link>
        </h3>
        <p className="text-sm text-[#7A4E2D]/70 line-clamp-2 flex-1">{product.description}</p>

        {/* Availability badge */}
        <div className="flex items-center gap-1.5">
          {product.is_available ? (
            <span className="badge-green">
              <CheckCircle className="w-3 h-3" />
              Disponible {product.stock > 0 ? `(${product.stock})` : ''}
            </span>
          ) : (
            <span className="badge-red">
              <XCircle className="w-3 h-3" />
              Agotado
            </span>
          )}
        </div>

        {/* Price & Actions */}
        <div className="flex items-center justify-between pt-2 mt-auto border-t border-[#7A4E2D]/10 gap-2">
          <span className="font-display font-bold text-[#7A4E2D] text-lg">
            {formatCOP(product.price)}
          </span>
          <div className="flex gap-2">
            <Link
              to={`/productos/${product.slug}`}
              className="p-2 bg-[#F6E7D8] hover:bg-[#F7D6E0] text-[#7A4E2D] rounded-lg transition-colors"
              aria-label={`Ver detalle de ${product.name}`}
            >
              <Eye className="w-4 h-4" />
            </Link>
            <button
              onClick={handleAddToCart}
              disabled={!product.is_available || added}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                added
                  ? 'bg-[#5F8D4E] text-white scale-95'
                  : product.is_available
                  ? 'bg-[#7A4E2D] hover:bg-[#67391F] text-white active:scale-95'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
              aria-label={user ? `Agregar ${product.name} al carrito` : `Iniciar sesión para ver ${product.name}`}
            >
              {added ? (
                <>✓ Agregado</>
              ) : (
                <>
                  <ShoppingBag className="w-3.5 h-3.5" />
                  {user ? 'Agregar' : 'Ver producto'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

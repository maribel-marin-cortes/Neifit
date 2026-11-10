import CatalogImage from '../components/CatalogImage';
import React from 'react';
import { Link } from 'react-router-dom';
import { Trash2, Plus, Minus, ShoppingBag, MessageCircle, ArrowLeft, FileText } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { formatCOP } from '../components/ProductCard';

export default function CarritoPage() {
  const { items, subtotal, shippingCost, total, updateQuantity, removeFromCart, clearCart, getWhatsAppOrderText } = useCart();

  if (items.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-4 text-center py-20">
        <div className="w-20 h-20 bg-[#FFF8F2] rounded-full flex items-center justify-center border-2 border-[#7A4E2D]/20">
          <ShoppingBag className="w-9 h-9 text-[#7A4E2D]/40" />
        </div>
        <h2 className="font-display font-bold text-2xl text-[#4B2E1F]">Tu carrito está vacío</h2>
        <p className="text-[#7A4E2D]/70 max-w-sm">
          Aún no has agregado productos. Explora nuestro catálogo y añade lo que más te guste.
        </p>
        <Link to="/catalogo" className="btn-primary px-8">
          <ShoppingBag className="w-4 h-4" />
          Ir al catálogo
        </Link>
      </div>
    );
  }

  const whatsappMsg = getWhatsAppOrderText();

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-extrabold text-3xl text-[#4B2E1F]">
            Carrito de compras
          </h1>
          <button
            onClick={clearCart}
            className="text-sm text-red-500 hover:text-red-700 flex items-center gap-1.5 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Vaciar carrito
          </button>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Items list */}
          <div className="lg:col-span-2 space-y-4">
            {items.map(item => (
              <div key={item.id} className="card-cream p-4 flex gap-4">
                <CatalogImage
                  src={item.image_url}
                  alt={item.name}
                  className="w-20 h-20 object-cover rounded-xl flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-[#5F8D4E] mb-0.5">{item.category_name}</p>
                  <h3 className="font-semibold text-[#4B2E1F] truncate">{item.name}</h3>
                  <p className="text-sm text-[#7A4E2D] font-medium">{formatCOP(item.price)} / unidad</p>
                  <div className="flex items-center gap-3 mt-3">
                    <div className="flex items-center border border-[#7A4E2D]/25 rounded-lg overflow-hidden text-sm">
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        className="px-2.5 py-1.5 text-[#7A4E2D] hover:bg-[#F6E7D8] transition-colors"
                        aria-label="Disminuir cantidad"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="px-3 py-1.5 font-bold text-[#4B2E1F] min-w-[2.5rem] text-center">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        className="px-2.5 py-1.5 text-[#7A4E2D] hover:bg-[#F6E7D8] transition-colors"
                        aria-label="Aumentar cantidad"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.id)}
                      className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      aria-label={`Eliminar ${item.name} del carrito`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="text-right flex flex-col justify-between">
                  <span className="font-display font-bold text-[#7A4E2D]">
                    {formatCOP(item.price * item.quantity)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Order summary */}
          <div className="lg:col-span-1">
            <div className="card-cream p-6 sticky top-24">
              <h2 className="font-display font-bold text-xl text-[#4B2E1F] mb-5">Resumen del pedido</h2>
              <div className="space-y-3 text-sm mb-5">
                <div className="flex justify-between text-[#7A4E2D]/80">
                  <span>Subtotal ({items.reduce((a,i) => a+i.quantity,0)} productos)</span>
                  <span className="font-semibold">{formatCOP(subtotal)}</span>
                </div>
                <div className="flex justify-between text-[#7A4E2D]/80">
                  <span>Domicilio estimado</span>
                  <span className="font-semibold">{formatCOP(shippingCost)}</span>
                </div>
                <div className="border-t border-[#7A4E2D]/15 pt-3 flex justify-between font-display font-bold text-lg text-[#4B2E1F]">
                  <span>Total</span>
                  <span>{formatCOP(total)}</span>
                </div>
              </div>

              <div className="space-y-3">
                <Link to="/checkout" className="btn-primary w-full justify-center py-3 text-base">
                  Finalizar pedido
                </Link>

                <a
                  href={`https://wa.me/573127827020?text=${whatsappMsg}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary w-full justify-center py-2.5"
                >
                  <MessageCircle className="w-4 h-4" />
                  Pedir por WhatsApp
                </a>

                <Link to="/cotizador" className="btn-outline w-full justify-center py-2.5 text-sm">
                  <FileText className="w-4 h-4" />
                  Solicitar cotización
                </Link>
              </div>

              <p className="text-xs text-[#7A4E2D]/50 mt-4 text-center leading-relaxed">
                El precio final y disponibilidad se confirmarán al procesar el pedido.
                Domicilio disponible en Medellín.
              </p>
            </div>
          </div>
        </div>

        <Link to="/catalogo" className="inline-flex items-center gap-2 text-[#7A4E2D] hover:underline text-sm font-medium mt-8">
          <ArrowLeft className="w-4 h-4" />
          Seguir comprando
        </Link>
      </div>
    </div>
  );
}


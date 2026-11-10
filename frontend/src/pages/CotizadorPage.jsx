import CatalogImage from '../components/CatalogImage';
import React, { useState, useEffect } from 'react';
import { useCart } from '../context/CartContext';
import { api } from '../services/api';
import { Loader2, CheckCircle, Plus, Minus, Trash2 } from 'lucide-react';
import { formatCOP } from '../components/ProductCard';

export default function CotizadorPage() {
  const [products, setProducts] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [form, setForm] = useState({ customer_name: '', customer_phone: '', customer_email: '', notes: '' });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [requestId] = useState(() => crypto.randomUUID());

  useEffect(() => {
    api.getProducts({ available: true }).then(setProducts).catch(err => setError(err.message));
  }, []);

  const addProduct = (product) => {
    setSelectedItems(prev => {
      const existing = prev.find(i => i.id === product.id);
      if (existing) {
        return prev.map(i => i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
  };

  const updateQty = (id, qty) => {
    if (qty <= 0) {
      setSelectedItems(prev => prev.filter(i => i.id !== id));
    } else {
      setSelectedItems(prev => prev.map(i => i.id === id ? { ...i, quantity: qty } : i));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedItems.length === 0) { setError('Agrega al menos un producto a tu cotización.'); return; }
    if (!form.customer_name.trim() || !form.customer_phone.trim()) {
      setError('Nombre y teléfono son obligatorios.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const quote = await api.createQuote({
        request_id: requestId,
        ...form,
        items: selectedItems.map(i => ({
          product_id: i.id,
          product_name: i.name,
          quantity: i.quantity,
          reference_price: i.price
        }))
      });
      setSuccess(quote);
    } catch (err) {
      setError(err.message || 'Error al enviar la cotización.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-20">
        <div className="card-cream p-10 max-w-md w-full text-center">
          <CheckCircle className="w-14 h-14 text-[#5F8D4E] mx-auto mb-4" />
          <h2 className="font-display font-bold text-2xl text-[#4B2E1F] mb-2">¡Cotización enviada!</h2>
          <p className="text-[#7A4E2D]/80 mb-2">Número de cotización:</p>
          <p className="font-display font-bold text-xl text-[#7A4E2D] mb-5">{success.quote_number}</p>
          <p className="text-sm text-[#7A4E2D]/70 mb-6">
            Nos pondremos en contacto contigo pronto para confirmar precios, disponibilidad y condiciones de entrega.
          </p>
          <a
            href={`https://wa.me/573127827020?text=${encodeURIComponent(`Hola Neifit, acabo de enviar una cotización ${success.quote_number} y quiero hacer seguimiento.`)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary w-full justify-center"
          >
            Hacer seguimiento por WhatsApp
          </a>
        </div>
      </div>
    );
  }

  const referenceTotal = selectedItems.reduce((acc, i) => acc + i.price * i.quantity, 0);

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display font-extrabold text-3xl text-[#4B2E1F] mb-2">Cotizador</h1>
          <p className="text-[#7A4E2D]/70">
            Solicita cotización para eventos, pedidos por mayor o empresas. Te contactaremos con precio y condiciones.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Product selector */}
          <div className="lg:col-span-2">
            <h2 className="font-semibold text-[#4B2E1F] mb-4">Selecciona productos</h2>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-2 custom-scroll">
              {products.filter(p => p.is_available).map(p => (
                <div key={p.id} className="card-cream p-3 flex items-center gap-3">
                  <CatalogImage
                    src={p.image_url}
                    alt={p.name}
                    className="w-12 h-12 object-cover rounded-lg flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-[#4B2E1F] truncate">{p.name}</p>
                    <p className="text-xs text-[#7A4E2D]/70">{p.category_name} · Ref. {formatCOP(p.price)}</p>
                  </div>
                  <button
                    onClick={() => addProduct(p)}
                    className="p-2 bg-[#7A4E2D] text-white rounded-lg hover:bg-[#67391F] transition-colors flex-shrink-0"
                    aria-label={`Agregar ${p.name} a la cotización`}
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            {/* Selected items */}
            {selectedItems.length > 0 && (
              <div className="mt-6">
                <h2 className="font-semibold text-[#4B2E1F] mb-4">Productos seleccionados</h2>
                <div className="space-y-2">
                  {selectedItems.map(item => (
                    <div key={item.id} className="card-cream p-3 flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm text-[#4B2E1F] truncate">{item.name}</p>
                        <p className="text-xs text-[#7A4E2D]/70">
                          Ref. {formatCOP(item.price)} × {item.quantity} = {formatCOP(item.price * item.quantity)}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button onClick={() => updateQty(item.id, item.quantity - 1)} className="p-1 rounded-lg hover:bg-[#F6E7D8] text-[#7A4E2D]"><Minus className="w-4 h-4" /></button>
                        <span className="font-bold text-[#4B2E1F] w-6 text-center">{item.quantity}</span>
                        <button onClick={() => updateQty(item.id, item.quantity + 1)} className="p-1 rounded-lg hover:bg-[#F6E7D8] text-[#7A4E2D]"><Plus className="w-4 h-4" /></button>
                        <button onClick={() => updateQty(item.id, 0)} className="p-1 rounded-lg hover:bg-red-50 text-red-400"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    </div>
                  ))}
                  <div className="text-right text-sm font-semibold text-[#7A4E2D] pr-2">
                    Referencia estimada: <span className="text-[#4B2E1F] font-bold">{formatCOP(referenceTotal)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Contact form */}
          <div>
            <h2 className="font-semibold text-[#4B2E1F] mb-4">Tus datos de contacto</h2>
            <form onSubmit={handleSubmit} className="card-cream p-5 space-y-4">
              {[
                { name: 'customer_name', label: 'Nombre *', type: 'text', required: true },
                { name: 'customer_phone', label: 'Teléfono / WhatsApp *', type: 'tel', required: true },
                { name: 'customer_email', label: 'Correo electrónico', type: 'email', required: false },
              ].map(f => (
                <div key={f.name}>
                  <label className="block text-sm font-medium text-[#4B2E1F] mb-1">{f.label}</label>
                  <input
                    type={f.type}
                    name={f.name}
                    value={form[f.name]}
                    onChange={e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))}
                    required={f.required}
                    className="w-full px-3 py-2 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F] text-sm"
                  />
                </div>
              ))}
              <div>
                <label className="block text-sm font-medium text-[#4B2E1F] mb-1">Mensaje o detalles adicionales</label>
                <textarea
                  name="notes"
                  value={form.notes}
                  onChange={e => setForm(p => ({ ...p, notes: e.target.value }))}
                  rows={3}
                  placeholder="Evento corporativo, fecha deseada, cantidad aproximada..."
                  className="w-full px-3 py-2 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F] text-sm resize-none"
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-3 py-2 text-sm">{error}</div>
              )}

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-2.5 disabled:opacity-60">
                {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Enviando...</> : 'Solicitar cotización'}
              </button>
              <p className="text-[10px] text-[#7A4E2D]/40 text-center">Los precios mostrados son referenciales y pueden variar según disponibilidad y volumen.</p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}


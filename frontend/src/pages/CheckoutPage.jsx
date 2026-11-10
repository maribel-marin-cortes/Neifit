import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { formatCOP } from '../components/ProductCard';
import { CheckCircle, Loader2 } from 'lucide-react';

const PAYMENT_METHODS = [
  { value: 'contraentrega', label: 'Pago contra entrega (efectivo)' },
  { value: 'transferencia', label: 'Transferencia bancaria / PSE' },
  { value: 'wompi', label: 'Wompi / Tarjeta (próximamente)' },
];

export default function CheckoutPage() {
  const { items, subtotal, shippingCost, total, clearCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
    email: user?.email || '',
    address: '',
    payment_method: 'contraentrega',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleChange = e => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.address.trim()) { setError('La dirección de entrega es obligatoria.'); return; }
    setLoading(true);
    setError(null);
    try {
      const orderPayload = {
        user_id: user?.id || 'guest',
        customer_name: form.full_name,
        customer_phone: form.phone,
        customer_email: form.email,
        address: form.address,
        payment_method: form.payment_method,
        notes: form.notes,
        subtotal,
        shipping_cost: shippingCost,
        total,
        items: items.map(i => ({
          product_id: i.id,
          product_name: i.name,
          quantity: i.quantity,
          unit_price: i.price,
          subtotal: i.price * i.quantity
        }))
      };
      const order = await api.createOrder(orderPayload);
      clearCart();
      setSuccess(order);
    } catch (err) {
      setError(err.message || 'Error al procesar el pedido. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4 py-20 text-center">
        <div className="card-cream p-10 max-w-lg w-full">
          <CheckCircle className="w-16 h-16 text-[#5F8D4E] mx-auto mb-5" />
          <h2 className="font-display font-extrabold text-3xl text-[#4B2E1F] mb-3">¡Pedido creado!</h2>
          <p className="text-[#7A4E2D]/80 mb-2">Número de pedido:</p>
          <p className="font-display font-bold text-2xl text-[#7A4E2D] mb-5">{success.order_number}</p>
          <p className="text-sm text-[#7A4E2D]/70 mb-8">
            Total a pagar: <strong>{formatCOP(success.total)}</strong><br />
            Forma de pago: <strong className="capitalize">{success.payment_method}</strong><br />
            Guarda tu número de pedido para rastrear tu entrega.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to={`/seguimiento?codigo=${success.order_number}`}
              className="btn-primary"
            >
              Rastrear pedido
            </Link>
            <Link to="/catalogo" className="btn-outline">
              Seguir comprando
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center">
        <p className="text-4xl">🛒</p>
        <h2 className="font-display font-bold text-2xl text-[#4B2E1F]">Tu carrito está vacío</h2>
        <Link to="/catalogo" className="btn-primary">Explorar catálogo</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="font-display font-extrabold text-3xl text-[#4B2E1F] mb-8">Finalizar pedido</h1>
        <form onSubmit={handleSubmit} className="grid lg:grid-cols-3 gap-8">
          {/* Delivery form */}
          <div className="lg:col-span-2 space-y-5">
            <div className="card-cream p-6">
              <h2 className="font-semibold text-[#4B2E1F] mb-4">Datos de entrega</h2>
              <div className="space-y-4">
                {[
                  { name: 'full_name', label: 'Nombre completo', type: 'text', required: true },
                  { name: 'phone', label: 'Teléfono / WhatsApp', type: 'tel', required: true },
                  { name: 'email', label: 'Correo electrónico', type: 'email', required: false },
                ].map(f => (
                  <div key={f.name}>
                    <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">
                      {f.label} {f.required && <span className="text-red-500">*</span>}
                    </label>
                    <input
                      type={f.type}
                      name={f.name}
                      value={form[f.name]}
                      onChange={handleChange}
                      required={f.required}
                      className="w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F]"
                    />
                  </div>
                ))}
                <div>
                  <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">
                    Dirección de entrega en Medellín <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    name="address"
                    value={form.address}
                    onChange={handleChange}
                    required
                    rows={2}
                    placeholder="Ej: Calle 10 # 43E - 22, El Poblado. Torre 2, apto 304."
                    className="w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F] resize-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#4B2E1F] mb-1.5">Notas adicionales</label>
                  <textarea
                    name="notes"
                    value={form.notes}
                    onChange={handleChange}
                    rows={2}
                    placeholder="Instrucciones especiales de entrega..."
                    className="w-full px-4 py-2.5 bg-[#F6E7D8]/40 border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F] resize-none"
                  />
                </div>
              </div>
            </div>

            <div className="card-cream p-6">
              <h2 className="font-semibold text-[#4B2E1F] mb-4">Forma de pago</h2>
              <div className="space-y-2">
                {PAYMENT_METHODS.map(m => (
                  <label key={m.value} className={`flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition-all ${form.payment_method === m.value ? 'border-[#7A4E2D] bg-[#F6E7D8]' : 'border-[#7A4E2D]/20 hover:bg-[#FFF8F2]'}`}>
                    <input
                      type="radio"
                      name="payment_method"
                      value={m.value}
                      checked={form.payment_method === m.value}
                      onChange={handleChange}
                      className="accent-[#7A4E2D]"
                    />
                    <span className="text-sm font-medium text-[#4B2E1F]">{m.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Summary sidebar */}
          <div className="card-cream p-6 self-start sticky top-24">
            <h2 className="font-display font-bold text-lg text-[#4B2E1F] mb-4">Resumen</h2>
            <div className="space-y-2 text-sm mb-4">
              {items.map(i => (
                <div key={i.id} className="flex justify-between text-[#7A4E2D]/80">
                  <span className="truncate flex-1 mr-2">{i.quantity}x {i.name}</span>
                  <span className="font-medium">{formatCOP(i.price * i.quantity)}</span>
                </div>
              ))}
              <div className="border-t border-[#7A4E2D]/15 pt-2 flex justify-between text-[#7A4E2D]/70">
                <span>Domicilio</span>
                <span>{formatCOP(shippingCost)}</span>
              </div>
              <div className="border-t border-[#7A4E2D]/15 pt-2 flex justify-between font-display font-bold text-lg text-[#4B2E1F]">
                <span>Total</span>
                <span>{formatCOP(total)}</span>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-3 text-base disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Procesando...</> : 'Confirmar pedido'}
            </button>
            <p className="text-[10px] text-center text-[#7A4E2D]/40 mt-3 leading-relaxed">
              Al confirmar aceptas que los precios y disponibilidad se verificarán en nuestro sistema.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}


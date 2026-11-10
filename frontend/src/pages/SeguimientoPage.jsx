import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Search, Package, Loader2, CheckCircle, Clock, Truck, AlertTriangle, XCircle } from 'lucide-react';

const STATUS_CONFIG = {
  recibido:        { label: 'Recibido',        icon: '📥', color: 'bg-blue-100 text-blue-700', done: true },
  confirmado:      { label: 'Confirmado',       icon: '✅', color: 'bg-green-100 text-green-700', done: true },
  en_preparacion:  { label: 'En preparación',   icon: '👩‍🍳', color: 'bg-yellow-100 text-yellow-700', done: true },
  empacado:        { label: 'Empacado',          icon: '📦', color: 'bg-amber-100 text-amber-700', done: true },
  despachado:      { label: 'Despachado',        icon: '🚚', color: 'bg-orange-100 text-orange-700', done: true },
  en_ruta:         { label: 'En ruta',           icon: '🛵', color: 'bg-blue-100 text-blue-700', done: true },
  entregado:       { label: 'Entregado ✓',       icon: '🎉', color: 'bg-green-100 text-green-700', done: true },
  novedad:         { label: 'Novedad',           icon: '⚠️', color: 'bg-red-100 text-red-700', done: false },
  cancelado:       { label: 'Cancelado',         icon: '❌', color: 'bg-gray-100 text-gray-600', done: false },
};

export default function SeguimientoPage() {
  const [searchParams] = useSearchParams();
  const [code, setCode] = useState(searchParams.get('codigo') || '');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    setOrder(null);
    try {
      const result = await api.getOrderByTrackingCode(code.trim());
      setOrder(result);
    } catch (err) {
      setError(err.message || 'No se encontró el pedido. Verifica el código.');
    } finally {
      setLoading(false);
    }
  };

  const currentStatus = order ? STATUS_CONFIG[order.order_status] : null;

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-10">
          <span className="text-4xl mb-3 block">📍</span>
          <h1 className="font-display font-extrabold text-3xl text-[#4B2E1F] mb-2">Rastrear mi pedido</h1>
          <p className="text-[#7A4E2D]/70">Ingresa el número de pedido que recibiste al confirmar tu compra.</p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-3 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7A4E2D]/50" />
            <input
              type="text"
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder="Ej: NF-2026-001"
              className="w-full pl-10 pr-4 py-3 bg-[#FFF8F2] border border-[#7A4E2D]/25 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-[#4B2E1F] uppercase tracking-widest placeholder-normal"
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary px-6 disabled:opacity-60">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Buscar'}
          </button>
        </form>

        {error && (
          <div className="card-cream p-6 text-center text-red-600">
            <AlertTriangle className="w-8 h-8 mx-auto mb-3 text-red-400" />
            <p className="font-semibold">{error}</p>
            <p className="text-sm text-[#7A4E2D]/60 mt-2">
              ¿Necesitas ayuda?{' '}
              <a href="https://wa.me/573127827020" target="_blank" rel="noopener noreferrer" className="text-[#5F8D4E] hover:underline font-semibold">
                Escríbenos por WhatsApp
              </a>
            </p>
          </div>
        )}

        {order && (
          <div className="space-y-5">
            {/* Order overview */}
            <div className="card-cream p-6">
              <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                <div>
                  <p className="text-xs text-[#7A4E2D]/60 uppercase tracking-wider mb-0.5">Número de pedido</p>
                  <h2 className="font-display font-extrabold text-2xl text-[#4B2E1F]">{order.order_number}</h2>
                </div>
                {currentStatus && (
                  <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${currentStatus.color}`}>
                    {currentStatus.icon} {currentStatus.label}
                  </span>
                )}
              </div>
              <div className="grid sm:grid-cols-2 gap-3 text-sm text-[#7A4E2D]/80">
                <div><span className="font-semibold text-[#4B2E1F]">Cliente:</span> {order.customer_name}</div>
                <div><span className="font-semibold text-[#4B2E1F]">Dirección:</span> {order.address}</div>
                <div><span className="font-semibold text-[#4B2E1F]">Pago:</span> <span className="capitalize">{order.payment_status} — {order.payment_method}</span></div>
                <div><span className="font-semibold text-[#4B2E1F]">Total:</span> {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(order.total)}</div>
                {order.assigned_delivery_name && (
                  <div className="sm:col-span-2">
                    <span className="font-semibold text-[#4B2E1F]">Mensajero asignado:</span> {order.assigned_delivery_name}
                  </div>
                )}
              </div>
            </div>

            {/* Timeline de trazabilidad */}
            {order.tracking_history?.length > 0 && (
              <div className="card-cream p-6">
                <h3 className="font-display font-semibold text-[#4B2E1F] mb-5">Historial de estados</h3>
                <ol className="relative border-l-2 border-[#7A4E2D]/20 space-y-5 ml-2">
                  {[...order.tracking_history].reverse().map((event, i) => {
                    const cfg = STATUS_CONFIG[event.status] || { label: event.status, icon: '•', color: 'bg-gray-100 text-gray-700' };
                    return (
                      <li key={i} className="ml-5">
                        <span className="absolute -left-2.5 flex items-center justify-center w-5 h-5 rounded-full bg-[#F6E7D8] border-2 border-[#7A4E2D]/30 text-xs">
                          {i === 0 ? '✓' : '·'}
                        </span>
                        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold mb-1 ${cfg.color}`}>
                          {cfg.icon} {cfg.label}
                        </div>
                        <p className="text-sm text-[#4B2E1F]">{event.message}</p>
                        <time className="text-xs text-[#7A4E2D]/50">
                          {new Date(event.timestamp).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}
                        </time>
                      </li>
                    );
                  })}
                </ol>
              </div>
            )}

            {/* Products in order */}
            {order.items?.length > 0 && (
              <div className="card-cream p-6">
                <h3 className="font-display font-semibold text-[#4B2E1F] mb-4">Productos del pedido</h3>
                <ul className="divide-y divide-[#7A4E2D]/10">
                  {order.items.map((item, i) => (
                    <li key={i} className="flex justify-between py-2 text-sm">
                      <span className="text-[#7A4E2D]/80">{item.quantity}× {item.product_name}</span>
                      <span className="font-semibold text-[#7A4E2D]">
                        {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(item.subtotal)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {!order && !loading && !error && (
          <div className="text-center py-10 text-[#7A4E2D]/40">
            <Package className="w-12 h-12 mx-auto mb-3" />
            <p className="text-sm">Ingresa tu código de pedido para ver el estado de tu entrega.</p>
            <p className="text-xs mt-2">Ejemplo de código: <strong>NF-2026-001</strong></p>
          </div>
        )}
      </div>
    </div>
  );
}


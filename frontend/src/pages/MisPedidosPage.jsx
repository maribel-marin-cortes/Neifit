import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Package, Clock } from 'lucide-react';

const STATUS_LABELS = {
  recibido: { label: 'Recibido', color: 'bg-blue-100 text-blue-700' },
  confirmado: { label: 'Confirmado', color: 'bg-green-100 text-green-700' },
  en_preparacion: { label: 'En preparación', color: 'bg-yellow-100 text-yellow-700' },
  empacado: { label: 'Empacado', color: 'bg-amber-100 text-amber-700' },
  despachado: { label: 'Despachado', color: 'bg-orange-100 text-orange-700' },
  en_ruta: { label: 'En ruta', color: 'bg-blue-100 text-blue-700' },
  entregado: { label: 'Entregado', color: 'bg-green-100 text-green-700' },
  novedad: { label: 'Novedad', color: 'bg-red-100 text-red-700' },
  cancelado: { label: 'Cancelado', color: 'bg-gray-100 text-gray-500' },
};

export default function MisPedidosPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getOrders()
      .then(setOrders)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-10 h-10 rounded-full border-4 border-[#7A4E2D] border-t-transparent" />
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center py-20">
        <Package className="w-14 h-14 text-[#7A4E2D]/30" />
        <h2 className="font-display font-bold text-2xl text-[#4B2E1F]">Aún no tienes pedidos</h2>
        <Link to="/catalogo" className="btn-primary">Explorar catálogo</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-display font-extrabold text-3xl text-[#4B2E1F] mb-8">Mis pedidos</h1>
        <div className="space-y-4">
          {orders.map(order => {
            const statusCfg = STATUS_LABELS[order.order_status] || { label: order.order_status, color: 'bg-gray-100 text-gray-600' };
            return (
              <div key={order.id} className="card-cream p-5">
                <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                  <div>
                    <p className="font-display font-bold text-lg text-[#4B2E1F]">{order.order_number}</p>
                    <p className="text-sm text-[#7A4E2D]/60 flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3" />
                      {new Date(order.created_at).toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${statusCfg.color}`}>
                    {statusCfg.label}
                  </span>
                </div>
                <div className="text-sm text-[#7A4E2D]/80 mb-3">
                  <span className="font-semibold text-[#4B2E1F]">Total:</span>{' '}
                  {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(order.total)}
                  {' · '}
                  <span className="capitalize">{order.payment_method}</span>
                </div>
                {order.items?.length > 0 && (
                  <ul className="text-xs text-[#7A4E2D]/70 mb-3 space-y-0.5">
                    {order.items.slice(0, 3).map((item, i) => (
                      <li key={i}>• {item.quantity}× {item.product_name}</li>
                    ))}
                    {order.items.length > 3 && <li>... y {order.items.length - 3} más</li>}
                  </ul>
                )}
                <Link
                  to={`/seguimiento?codigo=${order.order_number}`}
                  className="text-sm font-semibold text-[#7A4E2D] hover:underline"
                >
                  Ver trazabilidad →
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}


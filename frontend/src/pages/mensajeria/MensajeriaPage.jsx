import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { formatCOP } from '../../components/ProductCard';
import { Truck, AlertTriangle, Loader2, Package } from 'lucide-react';

const STATUS_OPTIONS = ['en_preparacion','empacado','despachado','en_ruta','entregado','novedad'];

export default function MensajeriaPage() {
  const { isMensajeria, isAdmin, user, hasPermission } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);

  const canAccess = isMensajeria || isAdmin;

  useEffect(() => {
    if (!canAccess) return;
    const filter = isMensajeria ? { delivery_user_id: user?.id } : {};
    api.getOrders(filter)
      .then(all => setOrders(all.filter(o => !['entregado','cancelado'].includes(o.order_status))))
      .finally(() => setLoading(false));
  }, [canAccess]);

  if (!canAccess) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center">
        <AlertTriangle className="w-12 h-12 text-red-400" />
        <h2 className="font-display font-bold text-2xl text-[#4B2E1F]">Acceso restringido</h2>
        <p className="text-[#7A4E2D]/70">Solo el personal de mensajería puede acceder a este panel.</p>
        <Link to="/" className="btn-primary">Ir al inicio</Link>
      </div>
    );
  }

  const updateStatus = async (orderId, newStatus, message = '') => {
    setUpdatingId(orderId);
    try {
      const updated = await api.updateOrderStatus(orderId, newStatus, message || `Estado actualizado a: ${newStatus.replace(/_/g,' ')}`);
      if (newStatus === 'entregado') {
        setOrders(prev => prev.filter(o => o.id !== orderId));
      } else {
        setOrders(prev => prev.map(o => o.id === updated.id ? updated : o));
      }
    } catch (err) {
      alert('Error al actualizar: ' + err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6E7D8]">
      {/* Header */}
      <div className="bg-[#5F8D4E] text-white px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Truck className="w-6 h-6" />
            <div>
              <h1 className="font-display font-bold text-lg text-white">Panel de Mensajería — Neifit</h1>
              <p className="text-white/70 text-xs">{user?.full_name}</p>
            </div>
          </div>
          <Link to="/" className="text-white/70 hover:text-white text-sm">← Sitio</Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display font-bold text-xl text-[#4B2E1F]">
            Pedidos activos asignados
            {orders.length > 0 && (
              <span className="ml-2 bg-[#7A4E2D] text-white text-xs font-bold px-2 py-0.5 rounded-full">{orders.length}</span>
            )}
          </h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#5F8D4E]" />
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-16">
            <Package className="w-12 h-12 text-[#7A4E2D]/30 mx-auto mb-3" />
            <p className="text-[#7A4E2D]/60 font-medium">No tienes pedidos activos asignados.</p>
          </div>
        ) : (
          <div className="space-y-5">
            {orders.map(order => (
              <div key={order.id} className="card-cream p-5">
                {/* Order header */}
                <div className="flex flex-wrap items-start justify-between gap-2 mb-4">
                  <div>
                    <p className="font-mono font-bold text-[#7A4E2D] text-lg">{order.order_number}</p>
                    <p className="font-bold text-[#4B2E1F]">{order.customer_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[#4B2E1F]">{formatCOP(order.total)}</p>
                    <p className="text-xs text-[#7A4E2D]/60 capitalize">{order.payment_method}</p>
                  </div>
                </div>

                {/* Address */}
                <div className="bg-[#F6E7D8] rounded-xl px-4 py-3 mb-4">
                  <p className="text-xs font-semibold text-[#7A4E2D] uppercase tracking-wide mb-1">📍 Dirección de entrega</p>
                  <p className="text-sm text-[#4B2E1F] font-medium">{order.address}</p>
                </div>

                {/* Contact */}
                <div className="flex flex-wrap gap-3 mb-4 text-sm">
                  {order.customer_phone && (
                    <a
                      href={`tel:${order.customer_phone}`}
                      className="flex items-center gap-1.5 bg-[#FFF8F2] border border-[#7A4E2D]/20 px-3 py-1.5 rounded-lg text-[#7A4E2D] hover:bg-[#F6E7D8] transition-colors"
                    >
                      📞 {order.customer_phone}
                    </a>
                  )}
                  {order.customer_phone && (
                    <a
                      href={`https://wa.me/${order.customer_phone.replace(/[^0-9]/g,'')}?text=${encodeURIComponent(`Hola ${order.customer_name}, soy el mensajero de Neifit. Voy en camino con tu pedido ${order.order_number}.`)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 bg-[#5F8D4E]/10 border border-[#5F8D4E]/20 px-3 py-1.5 rounded-lg text-[#5F8D4E] hover:bg-[#5F8D4E]/20 transition-colors"
                    >
                      💬 WhatsApp al cliente
                    </a>
                  )}
                </div>

                {/* Notes */}
                {order.notes && (
                  <div className="text-sm text-[#7A4E2D]/70 italic mb-4">
                    📝 {order.notes}
                  </div>
                )}

                {/* Products */}
                {order.items?.length > 0 && (
                  <div className="text-xs text-[#7A4E2D]/70 mb-4 space-y-0.5">
                    {order.items.map((item, i) => (
                      <p key={i}>• {item.quantity}× {item.product_name}</p>
                    ))}
                  </div>
                )}

                {/* Status update */}
                <div className="border-t border-[#7A4E2D]/15 pt-4">
                  <p className="text-xs font-semibold text-[#7A4E2D]/60 uppercase tracking-wide mb-2">Estado actual: <span className="capitalize font-bold text-[#7A4E2D]">{order.order_status.replace(/_/g,' ')}</span></p>
                  <div className="flex flex-wrap gap-2">
                    {STATUS_OPTIONS.filter(s => {
                      if (s === order.order_status) return false;
                      if (isAdmin) return true;
                      const permissions = { despachado: 'delivery.start', en_ruta: 'delivery.start', entregado: 'delivery.complete', novedad: 'delivery.issue' };
                      const from = { despachado: ['empacado'], en_ruta: ['despachado'], entregado: ['en_ruta'], novedad: ['empacado', 'despachado', 'en_ruta'] };
                      return permissions[s] && hasPermission(permissions[s]) && from[s].includes(order.order_status);
                    }).map(s => (
                      <button
                        key={s}
                        onClick={() => updateStatus(order.id, s)}
                        disabled={updatingId === order.id}
                        className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all disabled:opacity-50 ${
                          s === 'entregado'
                            ? 'bg-green-100 border-green-300 text-green-700 hover:bg-green-200'
                            : s === 'novedad'
                            ? 'bg-red-100 border-red-300 text-red-700 hover:bg-red-200'
                            : 'bg-[#FFF8F2] border-[#7A4E2D]/25 text-[#7A4E2D] hover:bg-[#F6E7D8]'
                        }`}
                      >
                        {updatingId === order.id ? <Loader2 className="w-3 h-3 animate-spin inline" /> : null}
                        {s.replace(/_/g,' ')}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


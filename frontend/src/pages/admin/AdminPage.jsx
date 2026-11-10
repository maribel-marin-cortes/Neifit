import CatalogImage from '../../components/CatalogImage';
import AccessManagement from './AccessManagement';
import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { formatCOP } from '../../components/ProductCard';
import {
  Package, Users, ShoppingBag, FileText, Settings,
  Plus, Edit3, Trash2, Check, X, AlertTriangle, Loader2, BarChart2
} from 'lucide-react';

const TABS = [
  { key: 'accesos', label: 'Roles y permisos', icon: Users },
  { key: 'dashboard', label: 'Dashboard', icon: BarChart2 },
  { key: 'productos', label: 'Productos', icon: Package },
  { key: 'pedidos', label: 'Pedidos', icon: ShoppingBag },
  { key: 'cotizaciones', label: 'Cotizaciones', icon: FileText },
];

const STATUS_OPTIONS = ['recibido','confirmado','en_preparacion','empacado','despachado','en_ruta','entregado','novedad','cancelado'];

export default function AdminPage() {
  const { isAdmin, user } = useAuth();
  const [searchParams] = useSearchParams();
  const requestedTab = searchParams.get('modulo') || 'dashboard';
  const tab = TABS.some(item => item.key === requestedTab) ? requestedTab : 'dashboard';
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAdmin) return;
    setLoading(true);
    Promise.all([
      api.getProducts(),
      api.getOrders(),
      api.getQuotes()
    ]).then(([prods, ords, quots]) => {
      setProducts(prods);
      setOrders(ords);
      setQuotes(quots);
    }).finally(() => setLoading(false));
  }, [isAdmin]);

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center py-20">
        <AlertTriangle className="w-12 h-12 text-red-400" />
        <h2 className="font-display font-bold text-2xl text-[#4B2E1F]">Acceso restringido</h2>
        <p className="text-[#7A4E2D]/70">Solo los administradores pueden acceder a este panel.</p>
        <Link to="/" className="btn-primary">Ir al inicio</Link>
      </div>
    );
  }

  const totalRevenue = orders.filter(o => o.payment_status === 'aprobado').reduce((a, o) => a + (o.total || 0), 0);
  const pendingOrders = orders.filter(o => !['entregado','cancelado'].includes(o.order_status)).length;
  const availableProducts = products.filter(p => p.is_available).length;

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      const updated = await api.updateOrderStatus(orderId, newStatus, `Estado actualizado por administrador a: ${newStatus}`);
      setOrders(prev => prev.map(o => o.id === updated.id ? updated : o));
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6E7D8]">
      {/* Admin Header */}
      <div className="bg-[#4B2E1F] text-white px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="font-display font-bold text-lg text-white">Panel Administrador — Neifit</h1>
            <p className="text-white/60 text-xs mt-0.5">Bienvenido, {user?.full_name || 'Admin'}</p>
          </div>
          <Link to="/" className="text-white/70 hover:text-white text-sm transition-colors">← Ir al sitio</Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#7A4E2D]" />
          </div>
        ) : (
          <>
            {tab === 'accesos' && <AccessManagement />}
            {/* DASHBOARD */}
            {tab === 'dashboard' && (
              <div className="space-y-6">
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { label: 'Productos activos', value: `${availableProducts} / ${products.length}`, icon: Package, color: 'text-[#7A4E2D]' },
                    { label: 'Pedidos pendientes', value: pendingOrders, icon: ShoppingBag, color: 'text-orange-600' },
                    { label: 'Total pedidos', value: orders.length, icon: BarChart2, color: 'text-[#5F8D4E]' },
                    { label: 'Ingresos aprobados', value: formatCOP(totalRevenue), icon: FileText, color: 'text-[#4B2E1F]' },
                  ].map(stat => (
                    <div key={stat.label} className="card-cream p-5">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-xs text-[#7A4E2D]/60 font-medium mb-1">{stat.label}</p>
                          <p className={`font-display font-bold text-2xl ${stat.color}`}>{stat.value}</p>
                        </div>
                        <stat.icon className={`w-8 h-8 ${stat.color} opacity-30`} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="card-cream p-6">
                  <h3 className="font-semibold text-[#4B2E1F] mb-4">Últimos pedidos</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[#7A4E2D]/15">
                          {['Número','Cliente','Estado','Total','Fecha'].map(h => (
                            <th key={h} className="text-left py-2 px-2 text-xs font-semibold text-[#7A4E2D]/60 uppercase tracking-wide">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#7A4E2D]/10">
                        {orders.slice(0, 8).map(o => (
                          <tr key={o.id} className="hover:bg-[#F6E7D8]/40 transition-colors">
                            <td className="py-3 px-2 font-mono text-xs font-bold text-[#7A4E2D]">{o.order_number}</td>
                            <td className="py-3 px-2 text-[#4B2E1F]">{o.customer_name}</td>
                            <td className="py-3 px-2">
                              <select
                                value={o.order_status}
                                onChange={e => updateOrderStatus(o.id, e.target.value)}
                                className="text-xs bg-transparent border-0 text-[#7A4E2D] font-semibold cursor-pointer focus:outline-none"
                              >
                                {STATUS_OPTIONS.map(s => (
                                  <option key={s} value={s}>{s.replace(/_/g,' ')}</option>
                                ))}
                              </select>
                            </td>
                            <td className="py-3 px-2 font-semibold text-[#4B2E1F]">{formatCOP(o.total)}</td>
                            <td className="py-3 px-2 text-[#7A4E2D]/60 text-xs">{new Date(o.created_at).toLocaleDateString('es-CO')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* PRODUCTOS */}
            {tab === 'productos' && (
              <div>
                <div className="flex items-center justify-between mb-5">
                  <h2 className="font-display font-bold text-xl text-[#4B2E1F]">Gestión de productos</h2>
                  <Link to="/admin/productos/nuevo" className="btn-primary py-2 px-4 text-sm">
                    <Plus className="w-4 h-4" /> Nuevo producto
                  </Link>
                </div>
                <div className="card-cream overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-[#F6E7D8]">
                        <tr>
                          {['Imagen','Nombre','Categoría','Precio','Stock','Estado','Acciones'].map(h => (
                            <th key={h} className="text-left py-3 px-4 text-xs font-semibold text-[#7A4E2D]/70 uppercase tracking-wide">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#7A4E2D]/10">
                        {products.map(p => (
                          <tr key={p.id} className="hover:bg-[#F6E7D8]/30 transition-colors">
                            <td className="py-3 px-4">
                              <CatalogImage src={p.image_url} alt={p.name} className="w-10 h-10 rounded-lg object-cover" />
                            </td>
                            <td className="py-3 px-4 font-medium text-[#4B2E1F] max-w-[160px] truncate">{p.name}</td>
                            <td className="py-3 px-4 text-[#7A4E2D]/70">{p.category_name}</td>
                            <td className="py-3 px-4 font-semibold text-[#7A4E2D]">{formatCOP(p.price)}</td>
                            <td className="py-3 px-4">
                              <span className={`font-bold ${p.stock === 0 ? 'text-red-500' : p.stock <= 5 ? 'text-amber-600' : 'text-green-600'}`}>
                                {p.stock}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <span className={`badge-${p.is_available ? 'green' : 'red'} text-[11px]`}>
                                {p.is_available ? '✓ Activo' : '✗ Agotado'}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex gap-2">
                                <Link to={`/admin/productos/${p.id}/editar`} className="p-1.5 text-[#7A4E2D] hover:bg-[#F6E7D8] rounded-lg transition-colors">
                                  <Edit3 className="w-4 h-4" />
                                </Link>
                                <button
                                  onClick={async () => {
                                    if (confirm(`¿Eliminar "${p.name}"?`)) {
                                      await api.deleteProduct(p.id);
                                      setProducts(prev => prev.filter(x => x.id !== p.id));
                                    }
                                  }}
                                  className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* PEDIDOS */}
            {tab === 'pedidos' && (
              <div>
                <h2 className="font-display font-bold text-xl text-[#4B2E1F] mb-5">Todos los pedidos</h2>
                <div className="space-y-4">
                  {orders.map(o => (
                    <div key={o.id} className="card-cream p-5">
                      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                        <div>
                          <p className="font-mono font-bold text-[#7A4E2D]">{o.order_number}</p>
                          <p className="font-semibold text-[#4B2E1F]">{o.customer_name}</p>
                          <p className="text-sm text-[#7A4E2D]/60">{o.address}</p>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <span className="font-bold text-[#4B2E1F]">{formatCOP(o.total)}</span>
                          <select
                            value={o.order_status}
                            onChange={e => updateOrderStatus(o.id, e.target.value)}
                            className="text-xs border border-[#7A4E2D]/25 rounded-lg px-2 py-1 bg-[#FFF8F2] text-[#4B2E1F] focus:outline-none"
                          >
                            {STATUS_OPTIONS.map(s => (
                              <option key={s} value={s}>{s.replace(/_/g,' ')}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-3 text-xs text-[#7A4E2D]/70">
                        <span>💳 {o.payment_method} — {o.payment_status}</span>
                        <span>📅 {new Date(o.created_at).toLocaleDateString('es-CO')}</span>
                        {o.assigned_delivery_name && <span>🚛 {o.assigned_delivery_name}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* COTIZACIONES */}
            {tab === 'cotizaciones' && (
              <div>
                <h2 className="font-display font-bold text-xl text-[#4B2E1F] mb-5">Cotizaciones recibidas</h2>
                <div className="space-y-4">
                  {quotes.length === 0 ? (
                    <div className="text-center py-12 text-[#7A4E2D]/50">
                      <FileText className="w-10 h-10 mx-auto mb-3" />
                      No hay cotizaciones aún.
                    </div>
                  ) : quotes.map(q => (
                    <div key={q.id} className="card-cream p-5">
                      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                        <div>
                          <p className="font-mono font-bold text-[#7A4E2D]">{q.quote_number}</p>
                          <p className="font-semibold text-[#4B2E1F]">{q.customer_name}</p>
                          <p className="text-sm text-[#7A4E2D]/60">{q.customer_phone} · {q.customer_email}</p>
                        </div>
                        <span className={`badge-${q.status === 'pendiente' ? 'pink' : 'green'}`}>
                          {q.status}
                        </span>
                      </div>
                      {q.notes && <p className="text-sm text-[#7A4E2D]/70 mb-3 italic">"{q.notes}"</p>}
                      {q.items?.length > 0 && (
                        <ul className="text-xs text-[#7A4E2D]/70 space-y-0.5">
                          {q.items.map((it, i) => (
                            <li key={i}>• {it.quantity}× {it.product_name} (ref. {formatCOP(it.reference_price)})</li>
                          ))}
                        </ul>
                      )}
                      <div className="mt-3 flex gap-3">
                        <a
                          href={`https://wa.me/${q.customer_phone?.replace(/[^0-9]/g,'')}?text=${encodeURIComponent(`Hola ${q.customer_name}, te contactamos de Neifit sobre tu cotización ${q.quote_number}.`)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#5F8D4E] font-semibold hover:underline"
                        >
                          Responder por WhatsApp →
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}


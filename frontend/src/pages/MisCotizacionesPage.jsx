import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { formatCOP } from '../components/ProductCard';
export default function MisCotizacionesPage() {
  const [quotes, setQuotes] = useState([]), [error, setError] = useState(''), [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true); setError('');
    try { setQuotes(await api.getQuotes()); } catch (e) { setError(e.message); } finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  return <main className="max-w-3xl mx-auto px-4 py-10 space-y-5">
    <h1 className="font-bold text-3xl">Mis cotizaciones</h1><button className="btn-outline" disabled={loading} onClick={load}>Actualizar</button>
    {error && <p role="alert">{error}</p>}{loading && <p>Cargando cotizaciones…</p>}
    {!loading && !error && !quotes.length && <p>Aún no tienes cotizaciones.</p>}
    {quotes.map(q => <article key={q.id} className="card-cream p-6 space-y-2">
      <h2 className="font-bold">{q.quote_number}</h2><p>Estado: {q.status}</p>
      {q.items?.map((item, index) => <p key={index}>{item.quantity} × {item.product_name}</p>)}
      {q.offered_total && <><p className="font-bold">Oferta total: {formatCOP(q.offered_total)}</p><p className="whitespace-pre-wrap">{q.offer_conditions}</p><p>Válida hasta: {new Date(q.offer_valid_until).toLocaleString('es-CO')}</p></>}
    </article>)}
  </main>;
}

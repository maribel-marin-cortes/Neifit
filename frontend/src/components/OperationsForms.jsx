import React, { useState } from 'react';
import { api } from '../services/api';
import { formatCOP } from './ProductCard';

export function QuoteOffer({ quote, onSaved }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  return <div className="mt-4 border-t pt-4">
    {quote.offered_total && <p>Oferta: <strong>{formatCOP(quote.offered_total)}</strong><br />{quote.offer_conditions}<br />Vigencia: {new Date(quote.offer_valid_until).toLocaleString('es-CO')}</p>}
    {['pendiente', 'respondida'].includes(quote.status) && <form className="space-y-2 mt-3" onSubmit={async e => {
      e.preventDefault(); const fields = new FormData(e.currentTarget); setBusy(true); setError('');
      try { onSaved(await api.respondQuote(quote.id, { total: fields.get('total'), conditions: fields.get('conditions'), valid_until: new Date(fields.get('valid_until')).toISOString() })); }
      catch (err) { setError(err.message); } finally { setBusy(false); }
    }}>
      <label className="block">Total final COP (incluye domicilio e impuestos aplicables)<input name="total" type="number" min="1" step="0.01" required className="input-field w-full" defaultValue={quote.offered_total || ''} /></label>
      <label className="block">Condiciones, entrega y forma de pago<textarea name="conditions" minLength={10} maxLength={3000} required className="input-field w-full" defaultValue={quote.offer_conditions || ''} /></label>
      <label className="block">Oferta válida hasta<input name="valid_until" type="datetime-local" required className="input-field w-full" /></label>
      <button disabled={busy} className="btn-primary">Guardar y avisar al cliente</button>
    </form>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
  </div>;
}

export function CashReceipt({ order, onSaved }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  if (order.payment_method !== 'contraentrega' || order.order_status !== 'entregado' || order.payment_status !== 'pendiente') return null;
  return <form className="mt-4 border-t pt-3 space-y-2" onSubmit={async e => {
    e.preventDefault(); const fields = new FormData(e.currentTarget); setBusy(true); setError('');
    try { onSaved(await api.confirmCash(order.id, { amount: fields.get('amount'), reference: fields.get('reference'), confirmed_received: fields.get('received') === 'on' })); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }}>
    <h3 className="font-bold">Registrar efectivo recibido</h3>
    <label className="block">Importe recibido COP<input name="amount" type="number" min="1" step="0.01" required className="input-field w-full" /></label>
    <label className="block">Referencia del recibo<input name="reference" minLength={3} maxLength={200} required className="input-field w-full" /></label>
    <label className="block"><input type="checkbox" name="received" required /> Confirmo que recibí efectivamente el dinero de este pedido.</label>
    <button disabled={busy} className="btn-primary">Confirmar cobro</button>
    {error && <p role="alert" className="text-red-700">{error}</p>}
  </form>;
}

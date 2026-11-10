import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
export default function SiteContentEditor() {
  const [content, setContent] = useState(null), [values, setValues] = useState([]), [settings, setSettings] = useState(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  useEffect(() => { Promise.all([api.getSiteContent(), api.getCompanyValues(), api.getCompanySettings()])
    .then(([text, entries, company]) => { setContent(text); setValues(entries); setSettings(company); }).catch(e => setError(e.message)); }, []);
  async function save(action) {
    setBusy(true); setError(''); setMessage('');
    try { await action(); setMessage('Cambios publicados. Actualiza la página de inicio para verlos.'); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <section className="space-y-6">
    <h2 className="font-bold text-2xl">Contenido institucional</h2>
    {error && <p role="alert" className="text-red-700">{error}</p>}{message && <p role="status">{message}</p>}
    {content && <form className="card-cream p-6 space-y-4" onSubmit={e => { e.preventDefault(); save(() => api.updateSiteContent(content)); }}>
      {Object.entries({ hero_title: 'Título principal', hero_description: 'Presentación', about_us: 'Quiénes somos', mission: 'Misión', vision: 'Visión' }).map(([key, label]) => <label key={key} className="block">{label}<textarea required maxLength={10000} className="input-field w-full" value={content[key] || ''} onChange={e => setContent({ ...content, [key]: e.target.value })} /></label>)}
      <button disabled={busy} className="btn-primary">Publicar textos</button>
    </form>}
    {settings && <form className="card-cream p-6 space-y-3" onSubmit={e => { e.preventDefault(); save(() => api.updateCompanySettings(Object.fromEntries(['business_name','phone_public','whatsapp_number','address','city','shipping_cost','opening_hours'].map(key => [key,settings[key]])))); }}>
      <h3 className="font-bold">Contacto y atención</h3>
      {Object.entries({ business_name: 'Nombre del negocio', phone_public: 'Teléfono público', whatsapp_number: 'WhatsApp (indicativo y número, solo dígitos)', address: 'Dirección del negocio', city: 'Ciudad', shipping_cost: 'Tarifa de domicilio COP' }).map(([key, label]) => <label key={key} className="block">{label}<input className="input-field w-full" type={key === 'shipping_cost' ? 'number' : 'text'} min={0} step={key === 'shipping_cost' ? '0.01' : undefined} required maxLength={300} value={settings[key] ?? ''} onChange={e => setSettings({ ...settings, [key]: e.target.value })} /></label>)}
      {['weekdays','weekends'].map(key => <label className="block" key={key}>{key === 'weekdays' ? 'Horario entre semana' : 'Fines de semana y festivos'}<input className="input-field w-full" maxLength={300} value={settings.opening_hours?.[key] || ''} onChange={e => setSettings({ ...settings, opening_hours: { ...settings.opening_hours, [key]: e.target.value } })} /></label>)}
      <button disabled={busy} className="btn-primary">Publicar contacto y tarifa</button>
    </form>}
    {values.length > 0 && <form className="card-cream p-6 space-y-4" onSubmit={e => { e.preventDefault(); save(() => api.updateCompanyValues(values)); }}>
      <h3 className="font-bold">Valores</h3>
      {values.map((value, index) => <fieldset key={value.id} className="space-y-2"><legend>Valor {index+1}</legend>
        <label className="block">Título<input className="input-field w-full" required maxLength={100} value={value.title} onChange={e => setValues(rows => rows.map((row, i) => i === index ? { ...row, title: e.target.value } : row))} /></label>
        <label className="block">Descripción<textarea className="input-field w-full" maxLength={3000} value={value.description || ''} onChange={e => setValues(rows => rows.map((row, i) => i === index ? { ...row, description: e.target.value } : row))} /></label>
      </fieldset>)}
      <button disabled={busy} className="btn-primary">Publicar valores</button>
    </form>}
  </section>;
}

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

const emptyAddress = { label: '', recipient: '', phone: '', address: '', city: '', notes: '' };
export default function MiCuentaPage() {
  const [account, setAccount] = useState(null);
  const [profile, setProfile] = useState({ full_name: '', phone: '' });
  const [address, setAddress] = useState(emptyAddress);
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function load() {
    const data = await api.getAccount();
    setAccount(data); setProfile({ full_name: data.full_name || '', phone: data.phone || '' });
  }
  useEffect(() => { load().catch(e => setError(e.message)); }, []);
  async function save(action, success) {
    setBusy(true); setError(''); setMessage('');
    try { await action(); await load(); setMessage(success); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
    <h1 className="font-display font-bold text-3xl">Mi cuenta</h1>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {message && <p role="status" className="text-green-800">{message}</p>}
    {!account ? <button className="btn-outline" onClick={() => load().catch(e => setError(e.message))}>Cargar mi cuenta</button> : <>
      <form className="card-cream p-6 space-y-4" onSubmit={e => { e.preventDefault(); save(() => api.updateAccount(profile), 'Perfil guardado.'); }}>
        <h2 className="text-xl font-bold">Datos personales</h2>
        <p>Correo: {account.email}</p>
        <label className="block">Nombre completo<input className="input-field w-full" required minLength={3} maxLength={100} autoComplete="name" value={profile.full_name} onChange={e => setProfile({ ...profile, full_name: e.target.value })} /></label>
        <label className="block">Teléfono<input className="input-field w-full" required minLength={7} maxLength={30} autoComplete="tel" value={profile.phone} onChange={e => setProfile({ ...profile, phone: e.target.value })} /></label>
        <button className="btn-primary" disabled={busy}>Guardar perfil</button>
        <Link to="/recuperar-contrasena" className="block underline">Cambiar mi contraseña por correo</Link>
      </form>
      <section className="card-cream p-6 space-y-4">
        <h2 className="text-xl font-bold">Direcciones guardadas</h2>
        {!account.addresses.length && <p>Aún no tienes direcciones guardadas.</p>}
        {account.addresses.map(item => <article key={item.id} className="border-b pb-3">
          <strong>{item.label}</strong><p>{item.address}, {item.city}</p><p>{item.recipient} · {item.phone}</p><p>{item.notes}</p>
          <button className="btn-outline mr-2" disabled={busy} onClick={() => { setEditing(item.id); setAddress(Object.fromEntries(Object.keys(emptyAddress).map(key => [key, item[key] || '']))); }}>Editar</button>
          <button className="btn-outline" disabled={busy} onClick={() => { if (window.confirm('¿Eliminar esta dirección guardada?')) save(() => api.deleteAddress(item.id), 'Dirección eliminada.'); }}>Eliminar</button>
        </article>)}
        <form className="space-y-3" onSubmit={e => { e.preventDefault(); save(async () => { await api.saveAddress(address, editing); setEditing(null); setAddress(emptyAddress); }, 'Dirección guardada.'); }}>
          <h3 className="font-bold">{editing ? 'Editar dirección' : 'Agregar dirección'}</h3>
          {Object.entries({ label: 'Nombre de la dirección', recipient: 'Persona que recibe', phone: 'Teléfono de contacto', address: 'Dirección completa', city: 'Ciudad', notes: 'Indicaciones adicionales' }).map(([key, label]) => <label key={key} className="block">{label}<input className="input-field w-full" value={address[key]} required={key !== 'notes'} minLength={key === 'phone' ? 7 : key === 'address' ? 5 : key === 'label' ? 2 : key === 'notes' ? 0 : 3} maxLength={key === 'notes' ? 500 : key === 'address' ? 300 : key === 'phone' ? 30 : key === 'label' ? 50 : 100} onChange={e => setAddress({ ...address, [key]: e.target.value })} /></label>)}
          <button className="btn-primary" disabled={busy}>Guardar dirección</button>
          {editing && <button type="button" className="btn-outline ml-2" onClick={() => { setEditing(null); setAddress(emptyAddress); }}>Cancelar edición</button>}
        </form>
        <p className="text-sm">Cambiar una dirección guardada no modifica pedidos anteriores. La cobertura de entrega se confirma al comprar.</p>
      </section>
    </>}
  </div>;
}

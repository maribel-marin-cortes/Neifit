import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function EmpresasPage() {
  const [companies, setCompanies] = useState([]);
  const [form, setForm] = useState({ name: '', slug: '' });
  const [error, setError] = useState('');

  async function load() {
    try { setCompanies(await api.getCompanies()); }
    catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function create(event) {
    event.preventDefault(); setError('');
    try {
      const company = await api.createCompany(form);
      api.selectCompany(company.slug);
      window.location.assign('/admin');
    } catch (e) { setError(e.message); }
  }

  function select(slug) {
    api.selectCompany(slug);
    window.location.assign('/?empresa=' + encodeURIComponent(slug));
  }

  return <main className="max-w-4xl mx-auto p-6 space-y-8">
    <div><h1 className="font-display text-3xl font-bold text-[#4B2E1F]">Mis empresas</h1>
      <p className="mt-2 text-[#7A4E2D]">Selecciona el comercio que deseas administrar o crea uno nuevo.</p></div>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-red-700">{error}</p>}
    <section className="grid gap-3 sm:grid-cols-2">
      {companies.map(({ company, role }) => <button key={company.id} onClick={() => select(company.slug)}
        className="text-left rounded-2xl border border-[#7A4E2D]/20 bg-white p-5 hover:bg-[#FFF8F2]">
        <strong className="block text-lg text-[#4B2E1F]">{company.nombre}</strong>
        <span className="text-sm text-[#7A4E2D]">{company.slug} · {role}</span>
        <span className="mt-2 block text-xs text-[#7A4E2D]">Enlace: /?empresa={company.slug}</span>
      </button>)}
    </section>
    <form onSubmit={create} className="rounded-2xl border border-[#7A4E2D]/20 bg-white p-6 space-y-4">
      <h2 className="text-xl font-bold text-[#4B2E1F]">Crear empresa</h2>
      <label className="block">Nombre<input required minLength="3" maxLength="100" className="input-field mt-1"
        value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
      <label className="block">Identificador de tienda<input required minLength="3" maxLength="63"
        pattern="[a-z0-9][a-z0-9-]*[a-z0-9]" placeholder="mi-empresa" className="input-field mt-1"
        value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value.toLowerCase() })} /></label>
      <button className="btn-primary" type="submit">Crear y administrar</button>
    </form>
  </main>;
}

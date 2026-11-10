import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../../services/api';

const initial = { name: '', slug: '', category_id: '', description: '', ingredients: '', allergens: '',
  price: '', stock: 0, image_url: '', featured: false, is_active: true, is_available: true };

export default function ProductEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(initial);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(null);
  const [categoryName, setCategoryName] = useState('');
  const [categorySlug, setCategorySlug] = useState('');
  useEffect(() => {
    let active = true;
    Promise.all([api.getCategories(), id ? api.getProductBySlug(id) : Promise.resolve(null)])
      .then(([rows, product]) => {
        if (!active) return;
        setCategories(rows);
        if (product) setVersion(product.updated_at);
        if (product) setForm({ ...initial, ...Object.fromEntries(Object.keys(initial).map(key => [key, product[key] ?? initial[key]])),
          // stock=0 no significa que el administrador haya deshabilitado el producto.
          is_available: product.sales_enabled ?? product.is_available });
        else if (rows.length) setForm(current => ({ ...current, category_id: rows[0].id }));
      }).catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);
  const input = 'w-full rounded-lg border border-[#7A4E2D]/30 bg-white px-3 py-2 mt-1';
  const change = e => setForm(current => ({ ...current, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));
  async function save(e) {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const payload = { ...form, price: Number(form.price), stock: Number(form.stock), ...(id ? { expected_updated_at: version } : {}) };
      if (!payload.slug) delete payload.slug;
      if (id) await api.updateProduct(id, payload); else await api.createProduct(payload);
      navigate('/admin?modulo=productos');
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }
  async function addCategory(e) {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const row = await api.createCategory({ name: categoryName, ...(categorySlug ? { slug: categorySlug } : {}), is_active: true });
      setCategories(current => [...current, row]); setForm(current => ({ ...current, category_id: row.id }));
      setCategoryName(''); setCategorySlug('');
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }
  return <div className="max-w-4xl mx-auto p-5 sm:p-8 space-y-6">
    <Link to="/admin?modulo=productos" className="text-sm underline">← Productos e inventario</Link>
    <h1 className="text-2xl font-bold">{id ? 'Editar producto' : 'Nuevo producto'}</h1>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {loading ? <p role="status">Cargando datos…</p> : <>
      <form onSubmit={save} className="card-cream p-5 space-y-5">
        <fieldset disabled={saving} className="grid sm:grid-cols-2 gap-4">
          <label>Nombre<input name="name" required minLength={3} maxLength={150} value={form.name} onChange={change} className={input} /></label>
          <label>Slug<input name="slug" pattern="[a-z0-9]+(-[a-z0-9]+)*" value={form.slug} onChange={change} placeholder="Se genera al crear si lo dejas vacío" className={input} /></label>
          <label>Categoría<select name="category_id" required value={form.category_id} onChange={change} className={input}><option value="">Seleccionar</option>{categories.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
          <label>Precio COP<input name="price" type="number" min="0.01" step="0.01" required value={form.price} onChange={change} className={input} /></label>
          <label>Stock<input name="stock" type="number" min="0" step="1" required value={form.stock} onChange={change} className={input} /></label>
          <label>Imagen<input name="image_url" value={form.image_url} onChange={change} placeholder="https://… o /images/postre-maracuya.png" className={input} /></label>
          <label className="sm:col-span-2">Descripción<textarea name="description" rows={3} value={form.description} onChange={change} className={input} /></label>
          <label>Ingredientes<textarea name="ingredients" value={form.ingredients} onChange={change} className={input} /></label>
          <label>Alérgenos<textarea name="allergens" value={form.allergens} onChange={change} className={input} /></label>
          <div className="flex flex-wrap gap-4 sm:col-span-2">{[['is_active','Activo'],['is_available','Habilitado para venta'],['featured','Destacado en inicio']].map(([key,label]) => <label key={key} className="flex gap-2 items-center"><input type="checkbox" name={key} checked={form[key]} onChange={change} />{label}</label>)}</div>
          <p className="sm:col-span-2 text-sm">Sin stock no se puede comprar. Desactivar conserva los pedidos históricos. Los precios y existencias deben corresponder al producto real.</p>
          <button type="submit" disabled={!categories.length} className="btn-primary justify-center">{saving ? 'Guardando…' : 'Guardar producto'}</button>
        </fieldset>
      </form>
      <details className="card-cream p-5"><summary className="cursor-pointer font-semibold">Crear categoría</summary><form onSubmit={addCategory} className="grid sm:grid-cols-2 gap-4 mt-4"><label>Nombre de categoría<input required minLength={3} value={categoryName} onChange={e => setCategoryName(e.target.value)} className={input} /></label><label>Slug de categoría<input pattern="[a-z0-9]+(-[a-z0-9]+)*" value={categorySlug} onChange={e => setCategorySlug(e.target.value)} className={input} /></label><button disabled={saving} className="btn-primary justify-center">Crear categoría</button></form></details>
    </>}
  </div>;
}

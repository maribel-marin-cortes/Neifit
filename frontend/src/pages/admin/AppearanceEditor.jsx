import React, { useEffect, useState } from 'react';
import { DEFAULT_THEME, useCompanyTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import { supabase } from '../../services/supabaseClient';

const COLORS = [
  ['primary_color','Color primario'],['secondary_color','Color secundario'],
  ['accent_color','Color de acento'],['background_color','Fondo'],
  ['surface_color','Superficie'],['text_color','Texto'],
];
const FONTS=['Poppins','Montserrat','Inter','Lora','Roboto'];

export default function AppearanceEditor() {
  const {theme,preview,save}=useCompanyTheme();
  const {user}=useAuth();
  const [form,setForm]=useState(theme); const [message,setMessage]=useState('');
  useEffect(() => setForm(theme),[theme]);
  const change=(key,value)=>{const next={...form,[key]:value};setForm(next);preview(next);};
  async function submit(event){event.preventDefault();setMessage('');try{await save(form);setMessage('Apariencia guardada.');}catch(e){setMessage(e.message);}}
  function reset(){setForm(DEFAULT_THEME);preview(DEFAULT_THEME);}
  async function upload(file,type){
    if(!file||!user?.company?.id||!supabase)return;
    if(!['image/jpeg','image/png','image/webp','image/svg+xml'].includes(file.type)||file.size>5*1024*1024){setMessage('Usa JPG, PNG, WebP o SVG de máximo 5 MB.');return;}
    setMessage('Subiendo imagen…');
    const extension=(file.name.split('.').pop()||'png').toLowerCase();
    const folder=type==='logo'?'logos':'portadas';
    const path=`empresas/${user.company.id}/${folder}/${crypto.randomUUID()}.${extension}`;
    const {error}=await supabase.storage.from('recursos-empresas').upload(path,file,{contentType:file.type,upsert:false});
    if(error){setMessage(error.message);return;}
    const {data}=supabase.storage.from('recursos-empresas').getPublicUrl(path);
    change(type==='logo'?'logo_url':'cover_url',data.publicUrl);setMessage('Imagen cargada; guarda el tema para publicarla.');
  }
  return <form onSubmit={submit} className="card-cream p-6 space-y-6">
    <div><h2 className="font-display text-xl font-bold">Apariencia de la empresa</h2>
      <p className="text-sm opacity-70">Los cambios se previsualizan antes de guardarlos.</p></div>
    {message && <p role="status" className="rounded-lg bg-white/60 p-3">{message}</p>}
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{COLORS.map(([key,label])=><label key={key} className="space-y-1">
      <span className="block text-sm font-medium">{label}</span><div className="flex gap-2">
      <input aria-label={label} type="color" value={form[key]} onChange={e=>change(key,e.target.value.toUpperCase())} className="h-11 w-14" />
      <input value={form[key]} pattern="^#[0-9A-Fa-f]{6}$" onChange={e=>change(key,e.target.value)} className="input-field" /></div></label>)}</div>
    <div className="grid gap-4 md:grid-cols-3">
      <label>Tipografía de títulos<select value={form.heading_font} onChange={e=>change('heading_font',e.target.value)} className="input-field mt-1">{FONTS.map(x=><option key={x}>{x}</option>)}</select></label>
      <label>Tipografía de texto<select value={form.body_font} onChange={e=>change('body_font',e.target.value)} className="input-field mt-1">{FONTS.map(x=><option key={x}>{x}</option>)}</select></label>
      <label>Radio de bordes ({form.border_radius}px)<input type="range" min="0" max="32" value={form.border_radius} onChange={e=>change('border_radius',Number(e.target.value))} className="w-full" /></label>
      <label>Botones<select value={form.button_style} onChange={e=>change('button_style',e.target.value)} className="input-field mt-1"><option value="solido">Sólido</option><option value="contorno">Contorno</option><option value="suave">Suave</option></select></label>
      <label className="md:col-span-2">URL del logo<input value={form.logo_url||''} onChange={e=>change('logo_url',e.target.value||null)} placeholder="/logo.png o https://…" className="input-field mt-1" /></label>
      <label>Cargar logo<input type="file" accept="image/jpeg,image/png,image/webp,image/svg+xml" onChange={e=>upload(e.target.files?.[0],'logo')} className="mt-1 block text-sm" /></label>
      <label className="md:col-span-2">URL de portada<input value={form.cover_url||''} onChange={e=>change('cover_url',e.target.value||null)} placeholder="https://…" className="input-field mt-1" /></label>
      <label>Cargar portada<input type="file" accept="image/jpeg,image/png,image/webp,image/svg+xml" onChange={e=>upload(e.target.files?.[0],'cover')} className="mt-1 block text-sm" /></label>
      <label className="flex items-center gap-2"><input type="checkbox" checked={form.published} onChange={e=>change('published',e.target.checked)} /> Tema publicado</label>
    </div>
    <div className="rounded-[var(--radius-company)] bg-[var(--color-background)] p-6 text-[var(--color-text)]">
      <h3 className="text-xl font-bold">Vista previa</h3><p>Así se verán las superficies, textos y botones de la empresa.</p>
      <button type="button" className="btn-primary mt-4">Botón principal</button>
    </div>
    <div className="flex gap-3"><button className="btn-primary" type="submit">Guardar y publicar</button><button className="btn-outline" type="button" onClick={reset}>Restablecer</button></div>
  </form>;
}

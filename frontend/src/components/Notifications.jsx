import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { api } from '../services/api';
export default function Notifications() {
  const [items, setItems] = useState([]), [error, setError] = useState('');
  useEffect(() => {
    let active = true, pending = false;
    async function load() {
      if (pending || document.hidden) return;
      pending = true;
      try { const rows = await api.getNotifications(); if (active) { setItems(rows); setError(''); } }
      catch { if (active) setError('No se pudieron actualizar los avisos.'); }
      finally { pending = false; }
    }
    load(); const timer = setInterval(load, 30000); window.addEventListener('focus', load);
    return () => { active = false; clearInterval(timer); window.removeEventListener('focus', load); };
  }, []);
  const unread = items.filter(item => !item.read_at).length;
  return <details className="relative">
    <summary className="cursor-pointer p-2 rounded-xl bg-[#FFF8F2] flex items-center" aria-label={`Avisos, ${unread} sin leer`}><Bell size={20} />{unread > 0 && <span className="text-xs ml-1">{unread}</span>}</summary>
    <div className="absolute right-0 mt-3 w-72 max-h-96 overflow-y-auto bg-[#FFF8F2] border rounded-xl shadow-xl p-3">
      <h2 className="font-bold">Avisos recientes</h2>{error && <p role="alert">{error}</p>}
      {!error && !items.length && <p>No tienes avisos.</p>}
      {items.map(item => <article key={item.id} className="border-b py-3 text-sm">
        <Link to={item.link} className={item.read_at ? '' : 'font-bold'}>{item.title}</Link><p>{item.message}</p>
        {!item.read_at && <button className="underline" onClick={async () => {
          try { await api.readNotification(item.id); setItems(rows => rows.map(row => row.id === item.id ? { ...row, read_at: new Date().toISOString() } : row)); }
          catch { setError('No se pudo marcar el aviso como leído.'); }
        }}>Marcar leído</button>}
      </article>)}
    </div>
  </details>;
}

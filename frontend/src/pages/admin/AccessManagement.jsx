import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const labels = { admin: 'Administrador', cliente: 'Cliente', mensajeria: 'Mensajero / domiciliario' };
export default function AccessManagement() {
  const { user } = useAuth();
  const [config, setConfig] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState('');
  async function load() { setConfig(await api.getAccessConfiguration()); }
  useEffect(() => { load().catch(() => setError('No se pudo cargar la gestión de accesos.')); }, []);
  async function save(role) {
    setBusy(true); setError(''); setNotice('');
    try {
      await api.updateRolePermissions(role.role, role.permissions);
      setNotice(`Permisos de ${labels[role.role]} guardados. Se aplican en la siguiente solicitud; el usuario puede recargar para actualizar su menú.`);
      await load();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function assign(id, role) {
    setBusy(true); setError(''); setNotice('');
    try { await api.assignUserRole(id, role); await load(); setNotice('Rol del usuario actualizado.'); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  if (!config) return <p role="status">{error || 'Cargando roles y permisos…'}</p>;
  return <section className="space-y-6">
    <h2 className="font-display font-bold text-2xl">Roles y permisos</h2>
    {!config.editable && <p role="status" className="card-cream p-4">La gestión de permisos aún no está habilitada. Aplica la migración indicada en GESTION_ROLES.md y activa RBAC_DATABASE_ENABLED en el backend. Mientras tanto se aplican los permisos base de cada rol.</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {notice && <p role="status" className="text-green-800">{notice}</p>}
    <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
      {config.roles.map(role => <fieldset key={role.role} className="card-cream p-5" disabled={busy || !config.editable || role.role === 'admin'}>
        <legend className="font-bold px-1">{labels[role.role]}</legend>
        {role.role === 'admin' && <p className="text-xs mb-3">Acceso completo protegido para evitar perder la administración.</p>}
        <div className="space-y-3">
          {role.allowed_permissions.map(code => <label key={code} className="flex gap-2 text-sm items-start">
            <input type="checkbox" className="mt-1 accent-[#7A4E2D]" checked={role.permissions.includes(code)} disabled={code === 'profile.read'} onChange={e => {
              setConfig(current => ({ ...current, roles: current.roles.map(r => r.role === role.role ? { ...r, permissions: e.target.checked ? [...r.permissions, code] : r.permissions.filter(p => p !== code) } : r) }));
            }} />
            <span>{config.permissions[code]}{code === 'profile.read' ? ' (obligatorio)' : ''}</span>
          </label>)}
        </div>
        {role.role !== 'admin' && <button type="button" onClick={() => save(role)} className="btn-primary mt-5 text-sm disabled:opacity-50">Guardar permisos</button>}
      </fieldset>)}
    </div>
    <div className="card-cream p-5 space-y-4">
      <h3 className="font-bold text-lg">Asignar rol a usuarios</h3>
      <p className="text-sm">Se muestran hasta 100 cuentas recientes. No puedes cambiar tu propio rol.</p>
      <label className="block text-sm">Buscar por nombre o correo<input type="search" value={filter} onChange={e => setFilter(e.target.value)} className="block w-full border rounded-lg px-3 py-2 mt-1" /></label>
      {config.users.length === 0 && <p>No hay usuarios disponibles para mostrar.</p>}
      <ul className="divide-y divide-[#7A4E2D]/15">
        {config.users.filter(u => `${u.full_name} ${u.email}`.toLowerCase().includes(filter.toLowerCase())).map(u => <li key={u.id} className="py-3 flex flex-wrap items-center gap-3 justify-between">
          <div className="min-w-0"><p className="font-medium">{u.full_name || 'Sin nombre'}</p><p className="text-sm break-all">{u.email}</p></div>
          <select aria-label={`Rol de ${u.email}`} value={u.role} disabled={busy || !config.editable || u.id === user.id} onChange={e => assign(u.id, e.target.value)} className="border rounded-lg px-3 py-2 bg-[#FFF8F2]">
            {Object.entries(labels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </li>)}
      </ul>
    </div>
  </section>;
}

import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const blankUser = { full_name: '', email: '', phone: '', password: '', role: 'mensajeria', email_verified_by_admin: false };
function Permissions({ codes, selected, descriptions, onChange, disabled }) {
  return <div className="space-y-3">{codes.map(code => <label key={code} className="flex gap-2 text-sm items-start">
    <input type="checkbox" className="mt-1 accent-[#7A4E2D]" disabled={disabled || code === 'profile.read'} checked={selected.includes(code)} onChange={e => onChange(e.target.checked ? [...selected, code] : selected.filter(p => p !== code))} />
    <span>{descriptions[code]}{code === 'profile.read' ? ' (obligatorio)' : ''}<code className="block text-xs text-[#7A4E2D]">{code}</code></span>
  </label>)}</div>;
}
export default function AccessManagement({ view = 'roles' }) {
  const { user } = useAuth();
  const [config, setConfig] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState('');
  const [person, setPerson] = useState(blankUser);
  const [roleForm, setRoleForm] = useState({ code: '', name: '', permissions: ['profile.read'] });
  async function load() { setConfig(await api.getAccessConfiguration()); }
  useEffect(() => { load().catch(err => setError(err.message)); }, []);
  async function run(operation, message) {
    setBusy(true); setError(''); setNotice('');
    try { await operation(); setNotice(message); await load(); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  if (!config) return <p role="status">{error || 'Cargando usuarios, roles y permisos…'}</p>;
  const disabled = busy || !config.editable;
  const roleName = code => config.roles.find(r => r.role === code)?.name || code;
  const inputClass = 'block w-full border rounded-lg px-3 py-2 mt-1 bg-white';
  return <section className="space-y-6">
    <h1 className="font-display font-bold text-2xl">{view === 'users' ? 'Usuarios' : 'Roles y permisos'}</h1>
    <p className="text-sm">Permiso del módulo: <code>{view === 'users' ? 'users.manage' : 'access.manage'}</code></p>
    {!config.editable && <p role="status" className="card-cream p-4">La gestión persistente no está habilitada. Sigue los pasos de GESTION_ROLES.md antes de registrar usuarios o guardar roles.</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {notice && <p role="status" className="text-green-800">{notice}</p>}
    {view === 'roles' ? <>
      <form className="card-cream p-5 space-y-4" onSubmit={e => {
        e.preventDefault();
        run(async () => { await api.createRole(roleForm); setRoleForm({ code: '', name: '', permissions: ['profile.read'] }); }, 'Rol creado. Ya puedes asignarlo a los usuarios.');
      }}>
        <h2 className="font-bold text-lg">Crear rol</h2>
        <fieldset disabled={disabled} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <label>Nombre del rol<input required minLength={3} maxLength={60} value={roleForm.name} onChange={e => setRoleForm({ ...roleForm, name: e.target.value })} className={inputClass} placeholder="Auxiliar de inventario" /></label>
            <label>Código del rol<input required pattern="[a-z][a-z0-9_]{2,39}" value={roleForm.code} onChange={e => setRoleForm({ ...roleForm, code: e.target.value })} className={inputClass} placeholder="auxiliar_inventario" /><span className="text-xs">Minúsculas, números y guion bajo; entre 3 y 40 caracteres.</span></label>
          </div>
          <Permissions codes={Object.keys(config.permissions).filter(p => !['access.manage', 'users.manage'].includes(p))} selected={roleForm.permissions} descriptions={config.permissions} onChange={permissions => setRoleForm({ ...roleForm, permissions })} />
          <button className="btn-primary" type="submit">Crear rol</button>
        </fieldset>
      </form>
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {config.roles.map(role => <fieldset key={role.role} className="card-cream p-5" disabled={disabled || role.role === 'admin'}>
          <legend className="font-bold px-1">{roleName(role.role)} <span className="text-xs">({role.role})</span></legend>
          {role.role === 'admin' && <p className="text-xs mb-3">Acceso completo protegido.</p>}
          <Permissions codes={role.allowed_permissions} selected={role.permissions} descriptions={config.permissions} onChange={permissions => setConfig(current => ({ ...current, roles: current.roles.map(r => r.role === role.role ? { ...r, permissions } : r) }))} />
          {role.role !== 'admin' && <button type="button" onClick={() => run(() => api.updateRolePermissions(role.role, role.permissions), `Permisos de ${roleName(role.role)} guardados.`)} className="btn-primary mt-5 text-sm">Guardar permisos</button>}
        </fieldset>)}
      </div>
    </> : <>
      <form className="card-cream p-5 space-y-4" onSubmit={e => {
        e.preventDefault();
        run(async () => { await api.createUser(person); setPerson({ ...blankUser }); }, 'Usuario registrado. Puede ingresar con su correo y contraseña. No se envió un correo automático.');
      }}>
        <h2 className="font-bold text-lg">Registrar usuario o mensajero</h2>
        <fieldset disabled={disabled} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <label>Nombre completo<input required minLength={3} maxLength={100} autoComplete="off" value={person.full_name} onChange={e => setPerson({ ...person, full_name: e.target.value })} className={inputClass} /></label>
            <label>Correo electrónico<input type="email" required maxLength={254} autoComplete="off" value={person.email} onChange={e => setPerson({ ...person, email: e.target.value })} className={inputClass} /></label>
            <label>Teléfono<input type="tel" required minLength={7} maxLength={30} value={person.phone} onChange={e => setPerson({ ...person, phone: e.target.value })} className={inputClass} /></label>
            <label>Contraseña inicial<input type="password" required minLength={8} maxLength={128} autoComplete="new-password" value={person.password} onChange={e => setPerson({ ...person, password: e.target.value })} className={inputClass} /></label>
            <label>Rol<select value={person.role} onChange={e => setPerson({ ...person, role: e.target.value })} className={inputClass}>{config.roles.map(r => <option key={r.role} value={r.role}>{roleName(r.role)}</option>)}</select></label>
          </div>
          <label className="flex gap-2 text-sm"><input type="checkbox" required checked={person.email_verified_by_admin} onChange={e => setPerson({ ...person, email_verified_by_admin: e.target.checked })} />He verificado que el correo pertenece a esta persona y autorizo su acceso.</label>
          <p className="text-sm">Comunica la contraseña directamente a la persona. Puede cambiarla mediante la recuperación de contraseña.</p>
          <button type="submit" className="btn-primary">Registrar usuario</button>
        </fieldset>
      </form>
      <div className="card-cream p-5 space-y-4">
        <h2 className="font-bold text-lg">Usuarios registrados</h2>
        <p className="text-sm">Se muestran hasta 100 cuentas recientes. No puedes cambiar tu propio rol.</p>
        <label className="block text-sm">Buscar por nombre o correo<input type="search" value={filter} onChange={e => setFilter(e.target.value)} className={inputClass} /></label>
        {config.users.length === 0 && <p>No hay usuarios disponibles para mostrar.</p>}
        <ul className="divide-y divide-[#7A4E2D]/15">{config.users.filter(u => `${u.full_name} ${u.email}`.toLowerCase().includes(filter.toLowerCase())).map(u => <li key={u.id} className="py-3 flex flex-wrap items-center gap-3 justify-between">
          <div className="min-w-0"><p className="font-medium">{u.full_name || 'Sin nombre'}</p><p className="text-sm break-all">{u.email}</p><p className="text-sm">{u.phone}</p></div>
          <select aria-label={`Rol de ${u.email}`} value={u.role} disabled={disabled || u.id === user.id} onChange={e => run(() => api.assignUserRole(u.id, e.target.value), 'Rol actualizado.')} className="border rounded-lg px-3 py-2 bg-[#FFF8F2]">{config.roles.map(r => <option key={r.role} value={r.role}>{roleName(r.role)}</option>)}</select>
        </li>)}</ul>
      </div>
    </>}
  </section>;
}

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Truck, CheckCircle, AlertCircle, Eye, EyeOff, Loader2, ArrowLeft, ShieldCheck, MapPin, Bike, Car, Footprints } from 'lucide-react';
import { api } from '../../services/api';

const VEHICLE_OPTIONS = [
  { id: 'moto', label: 'Motocicleta', icon: '🏍️', description: 'Ideal para entregas rápidas' },
  { id: 'bicicleta', label: 'Bicicleta', icon: '🚲', description: 'Ecológico para distancias cortas' },
  { id: 'carro', label: 'Automóvil', icon: '🚗', description: 'Para pedidos grandes o clima adverso' },
  { id: 'a_pie', label: 'A pie', icon: '🚶', description: 'Para zonas peatonales cercanas' },
];

export default function RegistroMensajeriaPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    document_id: '',
    vehicle_type: 'moto',
    vehicle_plate: '',
    city: 'Medellín',
    password: '',
    password_confirm: '',
    notes: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validaciones
    if (form.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    if (form.password !== form.password_confirm) {
      setError('Las contraseñas no coinciden. Por favor verifícalas.');
      return;
    }

    if (['moto', 'carro'].includes(form.vehicle_type) && !form.vehicle_plate.trim()) {
      setError('Por favor indica la placa del vehículo para motocicleta o automóvil.');
      return;
    }

    setLoading(true);

    try {
      // El backend crea la identidad bloqueada y solo el administrador puede activarla.
      await api.registerDeliveryRequest({
        full_name: form.full_name,
        email: form.email,
        phone: form.phone,
        document_id: form.document_id,
        vehicle_type: form.vehicle_type,
        vehicle_plate: form.vehicle_plate,
        city: form.city,
        password: form.password,
        notes: form.notes
      });

      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Ocurrió un error al procesar tu solicitud. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#F6E7D8] flex items-center justify-center p-4">
        <div className="card-cream max-w-lg w-full p-8 text-center space-y-6 shadow-xl border border-[#5F8D4E]/30 animate-in fade-in">
          <div className="w-20 h-20 bg-[#E8F3D6] rounded-full flex items-center justify-center mx-auto text-[#5F8D4E]">
            <CheckCircle className="w-12 h-12" />
          </div>

          <div className="space-y-2">
            <span className="inline-block px-3 py-1 bg-[#5F8D4E]/10 text-[#5F8D4E] text-xs font-bold rounded-full uppercase tracking-wider">
              Solicitud recibida
            </span>
            <h1 className="font-display font-bold text-2xl text-[#4B2E1F]">
              ¡Solicitud enviada con éxito!
            </h1>
            <p className="text-[#7A4E2D]/80 text-sm">
              Muchas gracias por postularte para ser parte del equipo de entregas de <strong>Neifit</strong>.
            </p>
          </div>

          <div className="bg-[#FFF8F2] border border-[#7A4E2D]/15 rounded-xl p-4 text-left text-xs space-y-2 text-[#4B2E1F]">
            <p className="font-bold flex items-center gap-1.5 text-sm text-[#7A4E2D]">
              <ShieldCheck className="w-4 h-4 text-[#5F8D4E]" /> Pasos para la activación:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-[#7A4E2D]/90">
              <li>El administrador de Neifit ha recibido una <strong>notificación inmediata</strong> para revisar tus datos.</li>
              <li>Tu cuenta se encuentra en estado <strong>Pendiente de aprobación</strong>.</li>
              <li>Una vez aprobada la solicitud, podrás iniciar sesión con tu correo (<strong>{form.email}</strong>) y accederás directamente al panel de entregas y pedidos asignados.</li>
            </ul>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row gap-3">
            <Link to="/login" className="btn-primary flex-1 text-center py-2.5">
              Ir a Iniciar sesión
            </Link>
            <Link to="/" className="px-4 py-2.5 rounded-xl border border-[#7A4E2D]/30 text-[#4B2E1F] text-sm font-semibold hover:bg-[#FFF8F2] transition-colors text-center">
              Volver al inicio
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6E7D8] py-12 px-4 sm:px-6">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Encabezado con navegación de regreso */}
        <div className="flex items-center justify-between">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-sm font-medium text-[#7A4E2D] hover:text-[#4B2E1F] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Volver al ingreso
          </Link>
          <Link to="/" className="text-xs text-[#7A4E2D]/60 hover:text-[#7A4E2D]">
            Neifit Tienda Saludable
          </Link>
        </div>

        {/* Tarjeta de bienvenida y branding de mensajería */}
        <div className="bg-[#5F8D4E] text-white rounded-2xl p-6 sm:p-8 shadow-lg flex flex-col sm:flex-row items-center gap-6">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center shrink-0">
            <Truck className="w-9 h-9 text-white" />
          </div>
          <div className="text-center sm:text-left">
            <span className="inline-block bg-white/20 text-white text-xs font-semibold px-2.5 py-0.5 rounded-full mb-2 uppercase tracking-wide">
              Área de Mensajería
            </span>
            <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">
              Registro para Repartidores
            </h1>
            <p className="text-white/80 text-sm mt-1 max-w-lg">
              Regístrate para realizar entregas de postres, snacks y bebidas naturales en Neifit. Tu solicitud será enviada al administrador para su aprobación.
            </p>
          </div>
        </div>

        {/* Formulario de registro */}
        <div className="card-cream p-6 sm:p-8 shadow-md">
          {error && (
            <div role="alert" className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">No pudimos procesar la solicitud</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Sección 1: Datos Personales */}
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#7A4E2D] mb-4 pb-1 border-b border-[#7A4E2D]/15">
                1. Información personal
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Nombre completo <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    minLength={3}
                    maxLength={100}
                    name="full_name"
                    value={form.full_name}
                    onChange={handleChange}
                    placeholder="Ej. Carlos Mario Rodríguez"
                    className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Documento de identidad (C.C.) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    minLength={5}
                    maxLength={30}
                    name="document_id"
                    value={form.document_id}
                    onChange={handleChange}
                    placeholder="Ej. 1037654321"
                    className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Correo electrónico <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="tu.correo@ejemplo.com"
                    className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Teléfono celular (WhatsApp) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    minLength={7}
                    maxLength={30}
                    name="phone"
                    value={form.phone}
                    onChange={handleChange}
                    placeholder="+57 300 1234567"
                    className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Ciudad / Zona de cobertura <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <MapPin className="w-4 h-4 text-[#7A4E2D]/50 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      name="city"
                      value={form.city}
                      onChange={handleChange}
                      placeholder="Medellín y Valle de Aburrá"
                      className="w-full pl-10 rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Sección 2: Vehículo y Logística */}
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#7A4E2D] mb-4 pb-1 border-b border-[#7A4E2D]/15">
                2. Medio de transporte y logística
              </h2>

              <div className="space-y-4">
                <label className="block text-xs font-semibold text-[#4B2E1F]">
                  Selecciona tu tipo de vehículo <span className="text-red-500">*</span>
                </label>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {VEHICLE_OPTIONS.map((v) => {
                    const isSelected = form.vehicle_type === v.id;
                    return (
                      <button
                        type="button"
                        key={v.id}
                        onClick={() => setForm(prev => ({ ...prev, vehicle_type: v.id }))}
                        className={`p-3.5 rounded-xl border text-center transition-all flex flex-col items-center gap-1.5 ${
                          isSelected
                            ? 'bg-[#E8F3D6] border-[#5F8D4E] text-[#4B2E1F] ring-2 ring-[#5F8D4E]/50 font-bold'
                            : 'bg-white border-[#7A4E2D]/20 text-[#4B2E1F]/70 hover:bg-[#FFF8F2]'
                        }`}
                      >
                        <span className="text-2xl">{v.icon}</span>
                        <span className="text-xs">{v.label}</span>
                      </button>
                    );
                  })}
                </div>

                {['moto', 'carro'].includes(form.vehicle_type) && (
                  <div>
                    <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                      Placa del vehículo <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      maxLength={20}
                      name="vehicle_plate"
                      value={form.vehicle_plate}
                      onChange={handleChange}
                      placeholder="Ej. ABC-12D"
                      className="w-full sm:w-1/2 uppercase font-mono rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Experiencia o notas adicionales (Opcional)
                  </label>
                  <textarea
                    rows={2}
                    maxLength={500}
                    name="notes"
                    value={form.notes}
                    onChange={handleChange}
                    placeholder="Disponibilidad horaria, experiencia con maletín térmico, etc."
                    className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                  />
                </div>
              </div>
            </div>

            {/* Sección 3: Seguridad de la Cuenta */}
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#7A4E2D] mb-4 pb-1 border-b border-[#7A4E2D]/15">
                3. Contraseña de acceso
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Contraseña <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      minLength={8}
                      maxLength={128}
                      name="password"
                      value={form.password}
                      onChange={handleChange}
                      placeholder="Mínimo 8 caracteres"
                      className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] pr-10 focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-[#7A4E2D]/60 hover:text-[#4B2E1F]"
                      aria-label="Ver u ocultar contraseña"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#4B2E1F] mb-1">
                    Confirmar contraseña <span className="text-red-500">*</span>
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    maxLength={128}
                    name="password_confirm"
                    value={form.password_confirm}
                    onChange={handleChange}
                    placeholder="Repite tu contraseña"
                    className="w-full rounded-xl border border-[#7A4E2D]/25 bg-white px-3.5 py-2.5 text-sm text-[#4B2E1F] focus:outline-none focus:ring-2 focus:ring-[#5F8D4E]"
                  />
                </div>
              </div>
            </div>

            {/* Aviso informativo de aprobación */}
            <div className="p-4 bg-[#FFF8F2] border border-[#7A4E2D]/15 rounded-xl text-xs text-[#7A4E2D] space-y-1">
              <p className="font-bold text-[#4B2E1F] flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#5F8D4E]" /> Proceso de aprobación:
              </p>
              <p>
                Al registrar tu solicitud, el administrador recibirá un aviso para autorizar tu cuenta. Una vez aprobada, se te asignará el rol de mensajería para que puedas gestionar y cambiar el estado de las entregas que te sean asignadas.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3.5 flex items-center justify-center gap-2 font-bold text-base shadow-md disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Enviando solicitud…
                </>
              ) : (
                <>
                  <Truck className="w-5 h-5" />
                  Enviar solicitud de mensajero
                </>
              )}
            </button>
          </form>

          {/* Enlaces al pie */}
          <div className="mt-8 pt-6 border-t border-[#7A4E2D]/15 text-center text-xs text-[#7A4E2D]/70 space-y-2">
            <p>
              ¿Ya tienes una cuenta aprobada?{' '}
              <Link to="/login" className="font-bold text-[#4B2E1F] hover:underline">
                Inicia sesión aquí
              </Link>
            </p>
            <p>
              ¿Eres un cliente que desea comprar postres y snacks?{' '}
              <Link to="/registro" className="font-bold text-[#5F8D4E] hover:underline">
                Crear cuenta de cliente
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


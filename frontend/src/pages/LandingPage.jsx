import CatalogImage from '../components/CatalogImage';
import { isIllustrativeImage } from '../services/catalogImages';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Star, MapPin, Phone, Clock, MessageCircle, ChevronDown } from 'lucide-react';
import { api } from '../services/api';
import ProductCard from '../components/ProductCard';
import { useCompanyTheme } from '../context/ThemeContext';

export default function LandingPage() {
  const { theme } = useCompanyTheme();
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [content, setContent] = useState({});
  const [values, setValues] = useState([]);
  const [settings, setSettings] = useState({});
  const [contentError, setContentError] = useState('');

  useEffect(() => {
    Promise.all([api.getSiteContent(), api.getCompanyValues(), api.getCompanySettings()])
      .then(([text, entries, company]) => { setContent(text); setValues(entries); setSettings(company); })
      .catch(() => setContentError('No se pudo cargar la información de la empresa. Intenta actualizar la página.'));
    api.getLandingProducts().then(list => {
      setFeaturedProducts(list.filter(p => p.featured).slice(0, 3));
    }).catch(() => setFeaturedProducts([]));
    api.getLandingCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  return (
    <div className="min-h-screen">
      {contentError && <p role="alert" className="p-4 text-red-700">{contentError}</p>}

      {/* ── HERO ─────────────────────────────── */}
      <section className="relative bg-gradient-to-br from-[#F6E7D8] via-[#FFF8F2] to-[#F7D6E0]/30 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32 flex flex-col lg:flex-row items-center gap-12">
          <div className="flex-1 text-center lg:text-left">
            <span className="inline-block badge-pink mb-4 text-sm font-semibold">🌿 {settings.city || ''}</span>
            <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl text-[#4B2E1F] leading-tight mb-6">
              {content.hero_title || settings.business_name || 'Neifit'}
            </h1>
            <p className="text-lg text-[#7A4E2D]/80 max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed">
              {content.hero_description}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
              <Link to="/catalogo" className="btn-primary text-base px-7 py-3 shadow-lg shadow-[#7A4E2D]/20">
                Explorar catálogo <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href={settings.whatsapp_url || undefined}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary text-base px-7 py-3"
              >
                <MessageCircle className="w-4 h-4" />
                WhatsApp
              </a>
            </div>
          </div>
          <div className="flex-1 flex justify-center">
            <div className="relative w-64 sm:w-80 lg:w-96 aspect-[3/2]">
              <div className="absolute inset-0 bg-[#D98CA4]/20 rounded-full blur-3xl"></div>
              <img
                src={theme.cover_url || theme.logo_url || '/logo-neifit-tropical.png'}
                alt="Portada de la empresa"
                className="relative w-full h-full object-contain rounded-2xl drop-shadow-2xl"
              />
            </div>
          </div>
        </div>
        <div className="text-center pb-6">
          <ChevronDown className="inline-block w-6 h-6 text-[#7A4E2D]/40 animate-bounce" />
        </div>
      </section>

      {/* ── QUIÉNES SOMOS ─────────────────────── */}
      <section id="quienes-somos" className="bg-[#FFF8F2] py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <span className="badge-green mb-4 inline-block">🤝 Quiénes somos</span>
          <h2 className="font-display font-bold text-3xl sm:text-4xl text-[#4B2E1F] mb-6">
            Conoce nuestra empresa
          </h2>
          <p className="text-lg text-[#7A4E2D]/80 leading-relaxed max-w-2xl mx-auto">
            {content.about_us}
          </p>
        </div>
      </section>

      {/* ── MISIÓN & VISIÓN ───────────────────── */}
      <section id="mision" className="py-20 px-4 bg-[#F6E7D8]">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          <div className="card-cream p-8 border-l-4 border-[#5F8D4E]">
            <h3 className="font-display font-bold text-xl text-[#4B2E1F] mb-3 flex items-center gap-2">
              <span className="text-2xl">🎯</span> Misión
            </h3>
            <p className="text-[#7A4E2D]/80 leading-relaxed">
              {content.mission}
            </p>
          </div>
          <div className="card-cream p-8 border-l-4 border-[#D98CA4]">
            <h3 className="font-display font-bold text-xl text-[#4B2E1F] mb-3 flex items-center gap-2">
              <span className="text-2xl">🔭</span> Visión
            </h3>
            <p className="text-[#7A4E2D]/80 leading-relaxed">
              {content.vision}
            </p>
          </div>
        </div>
      </section>

      {/* ── VALORES ───────────────────────────── */}
      <section id="valores" className="py-20 px-4 bg-[#FFF8F2]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <span className="badge-pink mb-3 inline-block">⭐ Nuestros valores</span>
            <h2 className="font-display font-bold text-3xl sm:text-4xl text-[#4B2E1F]">
              Lo que nos define
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
            {values.map((v) => (
              <div key={v.title} className="card-cream p-6 text-center hover:shadow-md transition-shadow">
                <div className="text-3xl mb-3">{'🌿'}</div>
                <h4 className="font-display font-semibold text-[#4B2E1F] mb-2">{v.title}</h4>
                <p className="text-sm text-[#7A4E2D]/70 leading-relaxed">{v.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CATEGORÍAS DESTACADAS ─────────────── */}
      <section id="categorias" className="py-20 px-4 bg-[#F6E7D8]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <span className="badge-green mb-3 inline-block">🛒 Nuestros productos</span>
            <h2 className="font-display font-bold text-3xl sm:text-4xl text-[#4B2E1F]">
              Categorías que te esperan
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {categories.map(cat => (
              <Link
                key={cat.id}
                to={`/catalogo?cat=${cat.slug}`}
                className="group relative overflow-hidden rounded-2xl shadow-md aspect-video"
              >
                <CatalogImage
                  src={cat.image}
                  alt={cat.name}
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#4B2E1F]/80 to-transparent"></div>
                {isIllustrativeImage(cat.image) && (
                  <span className="absolute top-2 right-2 rounded bg-[#FFF8F2]/95 px-2 py-1 text-[10px] text-[#4B2E1F]">Imagen ilustrativa</span>
                )}
                <div className="absolute bottom-0 left-0 right-0 p-5">
                  <h3 className="font-display font-bold text-white text-xl mb-1">{cat.name}</h3>
                  <p className="text-white/70 text-sm line-clamp-2">{cat.description}</p>
                  <span className="inline-flex items-center gap-1 mt-3 text-[#D98CA4] text-sm font-semibold group-hover:gap-2 transition-all">
                    Ver todos <ArrowRight className="w-4 h-4" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
          <div className="text-center">
            <Link to="/catalogo" className="btn-primary px-8 py-3 text-base">
              Ver catálogo completo <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── PRODUCTOS DESTACADOS ──────────────── */}
      {featuredProducts.length > 0 && (
        <section className="py-20 px-4 bg-[#FFF8F2]">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-10">
              <div>
                <span className="badge-pink mb-2 inline-block">⭐ Más pedidos</span>
                <h2 className="font-display font-bold text-3xl text-[#4B2E1F]">Productos destacados</h2>
              </div>
              <Link to="/catalogo" className="btn-outline hidden sm:flex">
                Ver todos <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredProducts.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </div>
        </section>
      )}

      {/* ── UBICACIÓN & CONTACTO ──────────────── */}
      <section id="contacto" className="py-20 px-4 bg-[#F6E7D8]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <span className="badge-green mb-3 inline-block">📍 Dónde encontrarnos</span>
            <h2 className="font-display font-bold text-3xl sm:text-4xl text-[#4B2E1F]">
              Ubicación y contacto
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-8 items-start">
            <div className="card-cream p-8 space-y-5">
              <div className="flex items-start gap-4">
                <MapPin className="w-5 h-5 text-[#7A4E2D] mt-1 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#4B2E1F]">Dirección</p>
                  <a
                    href={settings.map_search_url || undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#7A4E2D] hover:underline"
                  >
                    {settings.address}<br />{settings.city}
                  </a>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <Phone className="w-5 h-5 text-[#7A4E2D] flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#4B2E1F]">Teléfono / WhatsApp</p>
                  <a href={settings.phone_public ? `tel:${settings.phone_public}` : undefined} className="text-[#7A4E2D] hover:underline">{settings.phone_public}</a>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <Clock className="w-5 h-5 text-[#7A4E2D] mt-1 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#4B2E1F]">Horario de atención</p>
                  <p className="text-[#7A4E2D]/80">{settings.opening_hours?.weekdays}</p>
                  <p className="text-sm text-gray-400 mt-1">{settings.opening_hours?.weekends || 'Consultar atención en fines de semana y festivos'}</p>
                </div>
              </div>
              <div className="pt-2">
                <a
                  href={settings.whatsapp_url || undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary w-full justify-center"
                >
                  <MessageCircle className="w-4 h-4" />
                  Enviar mensaje por WhatsApp
                </a>
              </div>
            </div>

            <div className="card-cream overflow-hidden rounded-2xl">
              <a
                href={settings.map_search_url || undefined}
                target="_blank"
                rel="noopener noreferrer"
                className="block relative aspect-[4/3] bg-[#F6E7D8] hover:opacity-95 transition-opacity"
                aria-label="Abrir ubicación en Google Maps"
              >
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center p-6">
                  <MapPin className="w-12 h-12 text-[#7A4E2D]" />
                  <p className="font-display font-bold text-[#4B2E1F] text-lg">{settings.address}</p>
                  <p className="text-[#7A4E2D]">{settings.city}</p>
                  <span className="badge-green mt-2">Abrir en Google Maps →</span>
                </div>
              </a>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}


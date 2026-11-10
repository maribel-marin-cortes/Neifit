import React from 'react';
import { Link } from 'react-router-dom';

import { MessageCircle, MapPin, Phone, Clock, Instagram, Facebook } from 'lucide-react';

export default function Footer() {

  const year = new Date().getFullYear();

  return (
    <footer className="bg-[#4B2E1F] text-[#F6E7D8]">
      {/* WhatsApp Banner */}
      <div className="bg-[#5F8D4E] py-5 px-4 text-center">
        <a
          href="https://wa.me/573127827020"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-3 text-white font-semibold text-lg hover:opacity-90 transition-opacity"
        >
          <MessageCircle className="w-6 h-6" />
          ¿Tienes preguntas? Escríbenos por WhatsApp: +57 312 7827020
        </a>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
        {/* Brand Column */}
        <div>
          <img src="/logo-neifit-tropical.png" alt="Neifit" className="w-48 h-auto mb-4 rounded-xl" />
          <p className="text-sm text-[#D98CA4] leading-relaxed">
            Postres artesanales, snacks naturales y bebidas seleccionadas con el sabor de nuestras raíces colombianas.
          </p>
        </div>

        {/* Contact & Hours */}
        <div>
          <h3 className="font-semibold text-[#F6E7D8] mb-4 text-sm uppercase tracking-wider">Contacto</h3>
          <ul className="space-y-3 text-sm text-[#F6E7D8]/75">
            <li className="flex items-start gap-2">
              <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#D98CA4]" />
              <a
                href="https://www.google.com/maps/search/?api=1&query=CR+28B+%23+38F+-+56%2C+Medell%C3%ADn%2C+Colombia"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[#D98CA4] transition-colors"
              >
                CR 28B # 38F - 56<br />Medellín, Antioquia, Colombia
              </a>
            </li>
            <li className="flex items-center gap-2">
              <Phone className="w-4 h-4 flex-shrink-0 text-[#D98CA4]" />
              <a href="tel:+573127827020" className="hover:text-[#D98CA4] transition-colors">+57 312 7827020</a>
            </li>
            <li className="flex items-start gap-2">
              <Clock className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#D98CA4]" />
              <span>Lun – Vie: 9:00 a. m. – 6:00 p. m.<br /><span className="text-[#F6E7D8]/50">Fin de semana: No disponible</span></span>
            </li>
          </ul>
        </div>

        {/* Legal & Social */}
        <div>
          <h3 className="font-semibold text-[#F6E7D8] mb-4 text-sm uppercase tracking-wider">Legal</h3>
          <ul className="space-y-2 text-sm text-[#F6E7D8]/75 mb-6">
            <li><Link to="/politica-privacidad" className="hover:text-[#D98CA4] transition-colors">Política de Privacidad</Link></li>
            <li><Link to="/terminos" className="hover:text-[#D98CA4] transition-colors">Términos y Condiciones</Link></li>
            <li><Link to="/login" className="hover:text-[#D98CA4] transition-colors">Acceso al Sistema</Link></li>
          </ul>
          <div className="flex gap-3">
            <a
              href="https://www.instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Instagram Neifit"
              className="w-9 h-9 rounded-xl bg-[#F6E7D8]/10 hover:bg-[#D98CA4]/30 flex items-center justify-center transition-colors"
            >
              <Instagram className="w-4 h-4" />
            </a>
            <a
              href="https://www.facebook.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Facebook Neifit"
              className="w-9 h-9 rounded-xl bg-[#F6E7D8]/10 hover:bg-[#D98CA4]/30 flex items-center justify-center transition-colors"
            >
              <Facebook className="w-4 h-4" />
            </a>
            <a
              href="https://wa.me/573127827020"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="WhatsApp Neifit"
              className="w-9 h-9 rounded-xl bg-[#5F8D4E]/30 hover:bg-[#5F8D4E]/60 flex items-center justify-center transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>

      <div className="border-t border-[#F6E7D8]/10 py-5 px-4 text-center text-xs text-[#F6E7D8]/40">
        © {year} Neifit. Todos los derechos reservados. Medellín, Antioquia, Colombia.
        <span className="mx-2">·</span>
        Las descripciones de productos Fuxion están basadas en información oficial del fabricante y no constituyen afirmaciones médicas.
      </div>
    </footer>
  );
}

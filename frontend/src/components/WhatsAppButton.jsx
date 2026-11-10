import React from 'react';
import { MessageCircle } from 'lucide-react';

export default function WhatsAppButton() {
  return (
    <a
      href="https://wa.me/573127827020"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Contactar a Neifit por WhatsApp"
      className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-[#5F8D4E] hover:bg-[#4E7540] text-white rounded-full shadow-xl flex items-center justify-center transition-all hover:scale-110 active:scale-95"
    >
      <MessageCircle className="w-7 h-7" />
    </a>
  );
}

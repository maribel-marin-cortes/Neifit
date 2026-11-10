import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';
import { isSupabaseConfigured } from '../services/supabaseClient';

const CartContext = createContext();

const SHIPPING_FLAT_RATE = 5000; // Tarifa estándar de domicilio en Medellín

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try {
      const saved = localStorage.getItem('neifit_cart');
      const parsed = saved ? JSON.parse(saved) : [];
      // Retirar identificadores demo que no existen en el catálogo persistente.
      return isSupabaseConfigured ? parsed.filter(item => /^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(item.id)) : parsed;
    } catch {
      return [];
    }
  });
  const [shippingRate, setShippingRate] = useState(isSupabaseConfigured ? null : SHIPPING_FLAT_RATE);
  useEffect(() => {
    if (!isSupabaseConfigured) return;
    api.getCompanySettings().then(data => setShippingRate(Number(data.shipping_cost ?? SHIPPING_FLAT_RATE))).catch(() => setShippingRate(null));
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('neifit_cart', JSON.stringify(items));
    } catch (e) {
      console.error("Cart save error", e);
    }
  }, [items]);

  const addToCart = (product, quantity = 1) => {
    if (!product || !product.is_available || product.stock <= 0) {
      alert("Lo sentimos, este producto no tiene disponibilidad en este momento.");
      return false;
    }

    setItems(prevItems => {
      const existing = prevItems.find(item => item.id === product.id);
      if (existing) {
        const newQty = Math.min(existing.quantity + quantity, product.stock);
        return prevItems.map(item =>
          item.id === product.id ? { ...item, quantity: newQty } : item
        );
      } else {
        const initialQty = Math.min(quantity, product.stock);
        return [...prevItems, {
          id: product.id,
          name: product.name,
          slug: product.slug,
          price: product.price,
          image_url: product.image_url,
          category_name: product.category_name,
          stock: product.stock,
          quantity: initialQty
        }];
      }
    });
    return true;
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }

    setItems(prevItems =>
      prevItems.map(item => {
        if (item.id === productId) {
          const qty = Math.min(newQuantity, item.stock);
          return { ...item, quantity: qty };
        }
        return item;
      })
    );
  };

  const removeFromCart = (productId) => {
    setItems(prevItems => prevItems.filter(item => item.id !== productId));
  };

  const clearCart = () => {
    setItems([]);
  };

  const totalItemsCount = items.reduce((acc, item) => acc + item.quantity, 0);
  const subtotal = items.reduce((acc, item) => acc + (item.price * item.quantity), 0);
  const shippingCost = items.length > 0 ? (shippingRate ?? SHIPPING_FLAT_RATE) : 0;
  const total = subtotal + shippingCost;

  // Generador de mensaje para WhatsApp según requerimientos
  const getWhatsAppOrderText = (customerName = '', address = '') => {
    if (items.length === 0) return '';
    let msg = `*¡Hola Neifit! Deseo realizar este pedido:*%0A%0A`;
    if (customerName) msg += `*Cliente:* ${encodeURIComponent(customerName)}%0A`;
    if (address) msg += `*Dirección en Medellín:* ${encodeURIComponent(address)}%0A%0A`;
    msg += `*Productos:*%0A`;
    items.forEach(it => {
      msg += `• ${it.quantity}x ${encodeURIComponent(it.name)} - $${(it.price * it.quantity).toLocaleString('es-CO')}%0A`;
    });
    msg += `%0A*Subtotal:* $${subtotal.toLocaleString('es-CO')}`;
    msg += `%0A*Domicilio estimado:* $${shippingCost.toLocaleString('es-CO')}`;
    msg += `%0A*Total a pagar:* $${total.toLocaleString('es-CO')}`;
    msg += `%0A%0A_¿Me confirman disponibilidad y tiempos de entrega? ¡Gracias!_`;
    return msg;
  };

  return (
    <CartContext.Provider value={{
      items,
      totalItemsCount,
      subtotal,
      shippingCost,
      total,
      addToCart,
      updateQuantity,
      removeFromCart,
      clearCart,
      getWhatsAppOrderText
    }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) throw new Error("useCart must be used within a CartProvider");
  return context;
}


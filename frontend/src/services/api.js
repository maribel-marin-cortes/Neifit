import {
  initialCategories,
  initialProducts,
  initialOrders,
  initialQuotes,
  initialCompanySettings,
  initialSiteContent,
  initialCompanyValues
} from './mockData';
import { supabase, isSupabaseConfigured } from './supabaseClient';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
let sessionRefresh = null;

function activeCompanySlug() {
  const requested = typeof window === 'undefined' ? null
    : new URLSearchParams(window.location.search).get('empresa');
  if (requested && /^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$/.test(requested)) {
    localStorage.setItem('neifit_empresa', requested);
    return requested;
  }
  return localStorage.getItem('neifit_empresa') || 'neifit';
}

async function renewSession(rejectedToken) {
  if (!sessionRefresh) {
    sessionRefresh = (async () => {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) throw error;
      // Otra petición puede haber renovado la sesión mientras llegaba el 401.
      if (session?.access_token && session.access_token !== rejectedToken) return session;
      const result = await supabase.auth.refreshSession();
      if (result.error) throw result.error;
      if (!result.data.session?.access_token) throw new Error('Tu sesión ha caducado. Vuelve a iniciar sesión.');
      return result.data.session;
    })().finally(() => { sessionRefresh = null; });
  }
  return sessionRefresh;
}

// Helper for local state persistence when backend is offline
const getStored = (key, fallback) => {
  try {
    const item = localStorage.getItem(`neifit_${key}`);
    return item ? JSON.parse(item) : fallback;
  } catch {
    return fallback;
  }
};

const setStored = (key, value) => {
  try {
    localStorage.setItem(`neifit_${key}`, JSON.stringify(value));
  } catch (e) {
    console.error("Storage error:", e);
  }
};

// Request helper with automatic fallback
async function request(endpoint, options = {}) {
  try {
    let token;
    if (isSupabaseConfigured) {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) throw error;
      token = session?.access_token;
    } else {
      token = localStorage.getItem('neifit_token');
    }
    const headers = {
      'Content-Type': 'application/json',
      'X-Empresa': activeCompanySlug(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };

    let res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers
    });

    if (res.status === 401 && token && isSupabaseConfigured) {
      const session = await renewSession(token);
      res = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers: { ...headers, Authorization: `Bearer ${session.access_token}` },
      });
    }

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const detail = Array.isArray(errorData.detail) ? errorData.detail.map(item => item.msg).join('. ') : errorData.detail;
      const error = new Error(detail || `Error ${res.status}: ${res.statusText}`);
      error.status = res.status;
      error.code = res.headers?.get?.('X-Auth-Error') || errorData.code;
      throw error;
    }

    return await res.json();
  } catch (err) {
    console.warn(`[Neifit API] Falló la solicitud (${endpoint}):`, err.message);
    throw err;
  }
}

export const api = {
  getCompanies() { return request('/empresas'); },
  createCompany(data) { return request('/empresas', { method: 'POST', body: JSON.stringify(data) }); },
  selectCompany(slug) { localStorage.setItem('neifit_empresa', slug); },
  getNotifications() { return request('/notificaciones'); },
  readNotification(id) { return request(`/notificaciones/${id}/leer`, { method: 'PATCH' }); },
  respondQuote(id, data) { return request(`/cotizaciones/${id}/respuesta`, { method: 'POST', body: JSON.stringify(data) }); },
  confirmCash(id, data) { return request(`/pedidos/${id}/recibo-efectivo`, { method: 'POST', body: JSON.stringify(data) }); },
  getAccount() { return request('/cuenta'); },
  updateAccount(data) { return request('/cuenta', { method: 'PATCH', body: JSON.stringify(data) }); },
  saveAddress(data, id) { return request('/cuenta/direcciones' + (id ? '/' + id : ''), { method: id ? 'PUT' : 'POST', body: JSON.stringify(data) }); },
  deleteAddress(id) { return request('/cuenta/direcciones/' + id, { method: 'DELETE' }); },
  createCategory(data) { return request('/categorias/', { method: 'POST', body: JSON.stringify(data) }); },
  getDeliveryUsers() { return request('/pedidos/mensajeros'); },
  assignDelivery(orderId, userId) { return request(`/pedidos/${orderId}/mensajero`, { method: 'PATCH', body: JSON.stringify({ user_id: userId || null }) }); },
  updateQuoteStatus(quoteId, status) { return request(`/cotizaciones/${quoteId}/estado`, { method: 'PATCH', body: JSON.stringify({ status }) }); },
  createRole(data) { return request('/accesos/roles', { method: 'POST', body: JSON.stringify(data) }); },
  createUser(data) { return request('/accesos/usuarios', { method: 'POST', body: JSON.stringify(data) }); },
  getCurrentUser() { return request('/autenticacion/yo'); },
  getAccessConfiguration() { return request('/accesos/'); },
  updateRolePermissions(role, permissions) {
    return request(`/accesos/roles/${role}/permisos`, { method: 'PUT', body: JSON.stringify({ permissions }) });
  },
  assignUserRole(id, role) {
    return request(`/accesos/usuarios/${id}/rol`, { method: 'PATCH', body: JSON.stringify({ role }) });
  },
  async getLandingProducts() {
    try { return await request('/sitio/productos-destacados'); }
    catch (error) {
      if (isSupabaseConfigured) throw error;
      return initialProducts.filter(p => p.featured).slice(0, 3);
    }
  },
  async getLandingCategories() {
    try { return await request('/sitio/categorias'); }
    catch (error) {
      if (isSupabaseConfigured) throw error;
      return initialCategories;
    }
  },
  // Public & Site Settings
  async getCompanySettings() {
    try {
      return await request('/sitio/configuracion');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('settings', initialCompanySettings);
    }
  },

  async updateCompanySettings(data) {
    try {
      const res = await request('/sitio/configuracion', {
        method: 'PUT',
        body: JSON.stringify(data)
      });
      setStored('settings', res);
      return res;
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const current = getStored('settings', initialCompanySettings);
      const updated = { ...current, ...data };
      setStored('settings', updated);
      return updated;
    }
  },

  async getSiteContent() {
    try {
      return await request('/sitio/contenido');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('site_content', initialSiteContent);
    }
  },

  async updateSiteContent(data) {
    try {
      const res = await request('/sitio/contenido', {
        method: 'PUT',
        body: JSON.stringify(data)
      });
      setStored('site_content', res);
      return res;
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const current = getStored('site_content', initialSiteContent);
      const updated = { ...current, ...data };
      setStored('site_content', updated);
      return updated;
    }
  },

  async getCompanyValues() {
    try {
      return await request('/sitio/valores');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('company_values', initialCompanyValues);
    }
  },

  async updateCompanyValues(values) {
    try {
      const res = await request('/sitio/valores', {
        method: 'PUT',
        body: JSON.stringify(values)
      });
      setStored('company_values', res);
      return res;
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      setStored('company_values', values);
      return values;
    }
  },

  // Categories & Products
  async getCategories() {
    try {
      return await request('/categorias');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('categories', initialCategories);
    }
  },

  async getProducts(params = {}) {
    try {
      const searchParams = new URLSearchParams();
      if (params.category) searchParams.set('category', params.category);
      if (params.search) searchParams.set('search', params.search);
      for (const key of ['featured', 'available', 'include_inactive']) {
        if (typeof params[key] === 'boolean') searchParams.set(key, String(params[key]));
      }
      const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
      return await request(`/productos${query}`);
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      let list = getStored('products', initialProducts);
      if (params.category && params.category !== 'todos') {
        list = list.filter(p => p.category_slug === params.category || p.category_id === params.category);
      }
      if (params.search) {
        const q = params.search.toLowerCase();
        list = list.filter(p => p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q));
      }
      return list;
    }
  },

  async getProductBySlug(slug) {
    try {
      return await request(`/productos/${encodeURIComponent(slug)}`);
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const list = getStored('products', initialProducts);
      const found = list.find(p => p.slug === slug || p.id === slug);
      if (!found) throw new Error("Producto no encontrado");
      return found;
    }
  },

  async createProduct(productData) {
    try {
      const res = await request('/productos', {
        method: 'POST',
        body: JSON.stringify(productData)
      });
      return res;
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const list = getStored('products', initialProducts);
      const newProd = {
        ...productData,
        id: `prod-${Date.now()}`,
        slug: productData.slug || productData.name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        is_available: Number(productData.stock) > 0
      };
      const updated = [newProd, ...list];
      setStored('products', updated);
      return newProd;
    }
  },

  async updateProduct(id, productData) {
    try {
      return await request(`/productos/${id}`, {
        method: 'PUT',
        body: JSON.stringify(productData)
      });
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const list = getStored('products', initialProducts);
      const updated = list.map(p => p.id === id ? { ...p, ...productData, is_available: Number(productData.stock ?? p.stock) > 0 } : p);
      setStored('products', updated);
      return updated.find(p => p.id === id);
    }
  },

  async deleteProduct(id) {
    try {
      return await request(`/productos/${id}`, { method: 'DELETE' });
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const list = getStored('products', initialProducts);
      const updated = list.filter(p => p.id !== id);
      setStored('products', updated);
      return { success: true };
    }
  },

  // Orders & Tracking
  async createOrder(orderPayload) {
    try {
      return await request('/pedidos', {
        method: 'POST',
        body: JSON.stringify(orderPayload)
      });
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const orders = getStored('orders', initialOrders);
      const orderNumber = `NF-2026-${String(orders.length + 1).padStart(3, '0')}`;
      const newOrder = {
        id: `ord-${Date.now()}`,
        order_number: orderNumber,
        ...orderPayload,
        order_status: 'recibido',
        payment_status: 'pendiente',
        created_at: new Date().toISOString(),
        tracking_history: [
          { status: 'recibido', message: 'Pedido recibido en Neifit y en validación.', timestamp: new Date().toISOString() }
        ]
      };

      // Descontar inventario localmente
      const products = getStored('products', initialProducts);
      const updatedProducts = products.map(prod => {
        const item = orderPayload.items?.find(it => it.product_id === prod.id || it.id === prod.id);
        if (item) {
          const newStock = Math.max(0, prod.stock - item.quantity);
          return { ...prod, stock: newStock, is_available: newStock > 0 };
        }
        return prod;
      });
      setStored('products', updatedProducts);

      const updatedOrders = [newOrder, ...orders];
      setStored('orders', updatedOrders);
      return newOrder;
    }
  },

  async getOrders(roleFilter = {}) {
    try {
      return await request('/pedidos');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      let orders = getStored('orders', initialOrders);
      if (roleFilter.delivery_user_id) {
        orders = orders.filter(o => o.assigned_delivery_user_id === roleFilter.delivery_user_id);
      }
      return orders;
    }
  },

  async getOrderByTrackingCode(code) {
    try {
      return await request(`/seguimiento/${encodeURIComponent(code.trim())}`);
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const orders = getStored('orders', initialOrders);
      const cleanCode = code.trim().toUpperCase();
      const found = orders.find(o => o.order_number.toUpperCase() === cleanCode || o.id === code);
      if (!found) throw new Error("No encontramos ningún pedido con este código");
      return found;
    }
  },

  async updateOrderStatus(orderId, newStatus, message, novelties = null) {
    try {
      return await request(`/pedidos/${orderId}/estado`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus, message, novelties })
      });
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const orders = getStored('orders', initialOrders);
      const updated = orders.map(order => {
        if (order.id === orderId || order.order_number === orderId) {
          const history = order.tracking_history || [];
          return {
            ...order,
            order_status: newStatus,
            tracking_history: [
              ...history,
              { status: newStatus, message: message || `Estado actualizado a ${newStatus}`, timestamp: new Date().toISOString() }
            ]
          };
        }
        return order;
      });
      setStored('orders', updated);
      return updated.find(o => o.id === orderId || o.order_number === orderId);
    }
  },

  // Quotes (Cotizador)
  async createQuote(quoteData) {
    try {
      return await request('/cotizaciones', {
        method: 'POST',
        body: JSON.stringify(quoteData)
      });
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      const quotes = getStored('quotes', initialQuotes);
      const quoteNumber = `COT-2026-${String(quotes.length + 1).padStart(3, '0')}`;
      const newQuote = {
        id: `quot-${Date.now()}`,
        quote_number: quoteNumber,
        ...quoteData,
        status: 'pendiente',
        created_at: new Date().toISOString()
      };
      const updated = [newQuote, ...quotes];
      setStored('quotes', updated);
      return newQuote;
    }
  },

  async getQuotes() {
    try {
      return await request('/cotizaciones');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('quotes', initialQuotes);
    }
  }
};


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
      const error = new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
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
  getCurrentUser() { return request('/auth/me'); },
  getAccessConfiguration() { return request('/access/'); },
  updateRolePermissions(role, permissions) {
    return request(`/access/roles/${role}/permissions`, { method: 'PUT', body: JSON.stringify({ permissions }) });
  },
  assignUserRole(id, role) {
    return request(`/access/users/${id}/role`, { method: 'PATCH', body: JSON.stringify({ role }) });
  },
  async getLandingProducts() {
    try { return await request('/site/featured-products'); }
    catch (error) {
      if (isSupabaseConfigured) throw error;
      return initialProducts.filter(p => p.featured).slice(0, 3);
    }
  },
  async getLandingCategories() {
    try { return await request('/site/categories'); }
    catch (error) {
      if (isSupabaseConfigured) throw error;
      return initialCategories;
    }
  },
  // Public & Site Settings
  async getCompanySettings() {
    try {
      return await request('/site/settings');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('settings', initialCompanySettings);
    }
  },

  async updateCompanySettings(data) {
    try {
      const res = await request('/site/settings', {
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
      return await request('/site/content');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('site_content', initialSiteContent);
    }
  },

  async updateSiteContent(data) {
    try {
      const res = await request('/site/content', {
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
      return await request('/site/values');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('company_values', initialCompanyValues);
    }
  },

  async updateCompanyValues(values) {
    try {
      const res = await request('/site/values', {
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
      return await request('/categories');
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
      const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
      return await request(`/products${query}`);
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
      return await request(`/products/${slug}`);
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
      const res = await request('/products', {
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
      return await request(`/products/${id}`, {
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
      return await request(`/products/${id}`, { method: 'DELETE' });
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
      return await request('/orders', {
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
        payment_status: orderPayload.payment_method === 'contraentrega' ? 'pendiente' : 'aprobado',
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
      return await request('/orders');
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
      return await request(`/tracking/${code}`);
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
      return await request(`/orders/${orderId}/status`, {
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
      return await request('/quotes', {
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
      return await request('/quotes');
    } catch (error) {
      if (isSupabaseConfigured) throw error;
      return getStored('quotes', initialQuotes);
    }
  }
};


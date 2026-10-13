const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Product {
  id: number;
  name: string;
  slug: string;
  price: number;
  stock: number;
  description: string;
  image: string | null;
  category: Category;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface CategoryWithProducts extends Category {
  products: Omit<Product, 'description' | 'category'>[];
}

export interface OrderPayload {
  name: string;
  email: string;
  address: string;
  city: string;
  phone: string;
  // the server looks up prices itself; the client only says what and how many
  items: { product_id: number; quantity: number }[];
}

export interface Order {
  id: number;
  status: 'PENDING' | 'PAID' | 'CANCELLED';
  total_amount: number;
  payment: { provider: string; provider_order_id: string; amount: number; currency: string; key_id?: string };
}

export interface User {
  id: number;
  username: string;
  email: string;
}

// --- JWT handling: tokens live in localStorage and are sent as a Bearer header ---
const getToken = () => (typeof window === 'undefined' ? null : localStorage.getItem('access'));
const saveTokens = (access: string, refresh: string) => {
  localStorage.setItem('access', access);
  localStorage.setItem('refresh', refresh);
};
const clearTokens = () => {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
};

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `API Error: ${res.status}`);
  }
  return res.json();
}

export const getProducts = (params?: { category?: string; search?: string }) => {
  // only send filters that are actually set - "category=undefined" would match nothing
  const query = new URLSearchParams();
  if (params?.category) query.set('category', params.category);
  if (params?.search) query.set('search', params.search);
  const qs = query.toString();
  return fetchAPI<Product[]>(`/api/products/${qs ? '?' + qs : ''}`);
};
export const getProduct = (slug: string) => fetchAPI<Product>(`/api/products/${slug}/`);
export const getCategories = () => fetchAPI<Category[]>('/api/categories/');
export const getCategoryWithProducts = (slug: string) => fetchAPI<CategoryWithProducts>(`/api/categories/${slug}/`);
// idempotencyKey: send the same key when retrying so the order is never created twice
export const placeOrder = (payload: OrderPayload, idempotencyKey: string) =>
  fetchAPI<Order>('/orders/api/checkout/', {
    method: 'POST', body: JSON.stringify(payload), headers: { 'Idempotency-Key': idempotencyKey },
  });
export const payOrder = (orderId: number, paymentId: string, signature: string) =>
  fetchAPI<Order>(`/orders/api/orders/${orderId}/pay/`, {
    method: 'POST', body: JSON.stringify({ payment_id: paymentId, signature }),
  });
export const cancelOrder = (orderId: number) =>
  fetchAPI<Order>(`/orders/api/orders/${orderId}/cancel/`, { method: 'POST' });

type AuthResponse = { success: boolean; user: User; access: string; refresh: string };
export const loginUser = async (username: string, password: string) => {
  const res = await fetchAPI<AuthResponse>('/accounts/api/login/', {
    method: 'POST', body: JSON.stringify({ username, password }),
  });
  saveTokens(res.access, res.refresh);
  return res;
};
export const registerUser = async (data: { username: string; email: string; password1: string; password2: string }) => {
  const res = await fetchAPI<AuthResponse>('/accounts/api/register/', {
    method: 'POST', body: JSON.stringify(data),
  });
  saveTokens(res.access, res.refresh);
  return res;
};
export const logoutUser = async () => { clearTokens(); return { success: true }; };
export const getMe = () => {
  if (!getToken()) return Promise.reject(new Error('Not signed in'));
  return fetchAPI<User>('/accounts/api/me/');
};

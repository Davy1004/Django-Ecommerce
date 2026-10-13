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
  avg_rating?: number | null;
  review_count?: number;
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
  coupon_code?: string;
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

export interface OrderItem {
  product_id: number;
  product_name: string;
  unit_price: number;
  quantity: number;
  line_total: number;
}

export interface OrderDetail {
  id: number;
  status: 'PENDING' | 'PAID' | 'CANCELLED';
  subtotal: number;
  discount_amount: number;
  coupon_code: string;
  total_amount: number;
  name: string;
  email: string;
  address: string;
  city: string;
  phone: string;
  payment_provider: string;
  created_at: string;
  items: OrderItem[];
}

export interface Review {
  id: number;
  rating: number;
  title: string;
  body: string;
  author: string;
  verified_purchase: boolean;
  is_mine: boolean;
  created_at: string;
}

export interface ReviewsPayload {
  summary: { average: number | null; count: number; distribution: Record<'1' | '2' | '3' | '4' | '5', number> };
  results: Review[];
}

export interface CouponQuote {
  code: string;
  description: string;
  subtotal: number;
  discount: number;
  total: number;
}

export interface SalesDashboard {
  days: number;
  totals: {
    revenue: number; paid_orders: number; units_sold: number; average_order_value: number;
    discounts_given: number; customers: number; orders_by_status: Record<'PENDING' | 'PAID' | 'CANCELLED', number>;
  };
  range: { revenue: number; orders: number };
  daily: { date: string; revenue: number; orders: number }[];
  top_products: { name: string; units: number; revenue: number }[];
  by_category: { category: string; units: number; revenue: number }[];
  coupons: { code: string; orders: number; discount: number }[];
  low_stock: { id: number; name: string; slug: string; stock: number }[];
  recent_orders: { id: number; customer: string; status: 'PENDING' | 'PAID' | 'CANCELLED'; total: number; created_at: string }[];
  catalogue: { products: number; coupons_active: number; reviews: number; average_rating: number | null };
}

export interface Page<T> {
  count: number;
  results: T[];
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

/** Resolve to null instead of throwing, so a page can show "server is waking up" rather than crash. */
export async function safe<T>(p: Promise<T>): Promise<T | null> {
  try {
    return await p;
  } catch {
    return null;
  }
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_staff?: boolean;
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
    throw new ApiError(err.error || `API Error: ${res.status}`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const PAGE_SIZE = 12;

/** Plain list of products (no pagination); only sends the filters that are actually set. */
export const getProducts = (params?: { category?: string; search?: string; ordering?: string }) => {
  const qs = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => v && qs.set(k, v));
  return fetchAPI<Product[]>(`/api/products/${qs.size ? '?' + qs : ''}`);
};

export const getProductsPage = (params: { category?: string; search?: string; ordering?: string; page?: number; pageSize?: number }) => {
  const size = params.pageSize ?? PAGE_SIZE;
  const qs = new URLSearchParams({ limit: String(size), offset: String(((params.page ?? 1) - 1) * size) });
  (['category', 'search', 'ordering'] as const).forEach(k => params[k] && qs.set(k, params[k]!));
  return fetchAPI<Page<Product>>(`/api/products/?${qs}`);
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
export const getOrders = () => fetchAPI<OrderDetail[]>('/orders/api/orders/');
export const getOrder = (id: number | string) => fetchAPI<OrderDetail>(`/orders/api/orders/${id}/`);
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

// --- reviews ---
export const getReviews = (slug: string) => fetchAPI<ReviewsPayload>(`/api/products/${slug}/reviews/`);
export const saveReview = (slug: string, data: { rating: number; title: string; body: string }) =>
  fetchAPI<ReviewsPayload>(`/api/products/${slug}/reviews/`, { method: 'POST', body: JSON.stringify(data) });
export const deleteReview = (slug: string) => fetchAPI<void>(`/api/products/${slug}/reviews/`, { method: 'DELETE' });

// --- wishlist ---
export const getWishlist = () => fetchAPI<{ count: number; results: Product[] }>('/api/wishlist/');
export const addToWishlist = (productId: number) =>
  fetchAPI<{ product_id: number }>('/api/wishlist/', { method: 'POST', body: JSON.stringify({ product_id: productId }) });
export const removeFromWishlist = (productId: number) => fetchAPI<void>(`/api/wishlist/${productId}/`, { method: 'DELETE' });

// --- coupons & admin ---
export const previewCoupon = (code: string, items: { product_id: number; quantity: number }[]) =>
  fetchAPI<CouponQuote>('/orders/api/coupons/validate/', { method: 'POST', body: JSON.stringify({ code, items }) });
export const getSalesDashboard = (days = 30) => fetchAPI<SalesDashboard>(`/api/admin/sales/?days=${days}`);

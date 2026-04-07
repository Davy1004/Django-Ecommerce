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
  total_amount: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
}

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `API Error: ${res.status}`);
  }
  return res.json();
}

export const getProducts = (params?: { category?: string; search?: string }) => {
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  return fetchAPI<Product[]>(`/api/products/${qs ? '?' + qs : ''}`);
};
export const getProduct = (slug: string) => fetchAPI<Product>(`/api/products/${slug}/`);
export const getCategories = () => fetchAPI<Category[]>('/api/categories/');
export const getCategoryWithProducts = (slug: string) => fetchAPI<CategoryWithProducts>(`/api/categories/${slug}/`);
export const placeOrder = (payload: OrderPayload) =>
  fetchAPI<{ success: boolean; order_id: number; message: string }>('/orders/api/checkout/', {
    method: 'POST', body: JSON.stringify(payload),
  });
export const loginUser = (username: string, password: string) =>
  fetchAPI<{ success: boolean; user: User }>('/accounts/api/login/', {
    method: 'POST', body: JSON.stringify({ username, password }),
  });
export const registerUser = (data: { username: string; email: string; password1: string; password2: string }) =>
  fetchAPI<{ success: boolean; user: User }>('/accounts/api/register/', {
    method: 'POST', body: JSON.stringify(data),
  });
export const logoutUser = () => fetchAPI<{ success: boolean }>('/accounts/api/logout/', { method: 'POST' });
export const getMe = () => fetchAPI<User>('/accounts/api/me/');

import type { Product } from './api';

export const inr = (n: number) =>
  '₹' + n.toLocaleString('en-IN', { minimumFractionDigits: Number.isInteger(n) ? 0 : 2, maximumFractionDigits: 2 });

export const slugify = (s: string) =>
  s.toLowerCase().replace(/[^\w\s-]/g, '').trim().replace(/[\s_]+/g, '-').replace(/-+/g, '-');

/** Uploaded photo if the shop owner added one, otherwise the illustration shipped with the frontend. */
export const productImage = (p: { image: string | null; slug: string }) => p.image || `/products/${p.slug}.svg`;

/** Each category tile borrows the illustration of one of its products. */
export const CATEGORY_COVER: Record<string, string> = {
  electronics: 'smart-watch',
  books: 'clean-code',
  home: 'led-desk-lamp',
  fashion: 'running-sneakers',
  fitness: 'yoga-mat',
  stationery: 'fountain-pen',
};
export const categoryImage = (slug: string) => `/products/${CATEGORY_COVER[slug] ?? 'hardcover-notebook'}.svg`;

export const SORTS = [
  { value: '', label: 'Newest first' },
  { value: 'price', label: 'Price: low to high' },
  { value: '-price', label: 'Price: high to low' },
  { value: 'rating', label: 'Top rated' },
  { value: 'name', label: 'Name: A to Z' },
] as const;

export const stockLabel = (p: Pick<Product, 'stock'>) =>
  p.stock === 0 ? 'Out of stock' : p.stock <= 5 ? `Only ${p.stock} left` : 'In stock';

export const fmtDay = (iso: string) => new Date(iso + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
export const timeAgo = (iso: string) => {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days < 1) return 'today';
  if (days < 30) return `${days} day${days > 1 ? 's' : ''} ago`;
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};

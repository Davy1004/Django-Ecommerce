import type { Product } from './api';

export const inr = (n: number) =>
  '₹' + n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });

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
  { value: 'name', label: 'Name: A to Z' },
] as const;

export const stockLabel = (p: Pick<Product, 'stock'>) =>
  p.stock === 0 ? 'Out of stock' : p.stock <= 5 ? `Only ${p.stock} left` : 'In stock';

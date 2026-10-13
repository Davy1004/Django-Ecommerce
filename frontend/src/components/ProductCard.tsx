'use client';
import Link from 'next/link';
import { Product } from '@/lib/api';
import { productImage, inr } from '@/lib/format';
import { useCart } from '@/context/CartContext';
import { useToast } from '@/context/ToastContext';
import { ShoppingCart } from 'lucide-react';

export default function ProductCard({ product }: { product: Omit<Product, 'category' | 'description'> & Partial<Pick<Product, 'category' | 'description'>> }) {
  const { addItem } = useCart();
  const { show } = useToast();
  const out = product.stock === 0;

  const handleAdd = (e: React.MouseEvent) => {
    e.preventDefault();
    addItem({ id: product.id, name: product.name, price: product.price, image: product.image, slug: product.slug, stock: product.stock });
    show(`${product.name} added to cart`);
  };

  return (
    <Link href={`/products/${product.slug}`} className="group tile block">
      <div className="card overflow-hidden transition-all duration-300 group-hover:-translate-y-1" style={{ boxShadow: undefined }}>
        <div className="relative overflow-hidden" style={{ aspectRatio: '1 / 1', background: 'var(--card-img-bg)' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={productImage(product)} alt={product.name} loading="lazy" className="tile-img w-full h-full object-cover" />
          {out && <span className="badge absolute top-3 left-3" style={{ background: '#1a1208', color: '#fff' }}>Sold out</span>}
          {!out && product.stock <= 5 && <span className="badge absolute top-3 left-3 badge-pending">Only {product.stock} left</span>}
        </div>
        <div className="p-4">
          {product.category && <p className="eyebrow" style={{ fontSize: '0.68rem', marginBottom: 4 }}>{product.category.name}</p>}
          <h3 className="line-clamp-2 mb-3" style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', lineHeight: 1.3, minHeight: '2.7rem' }}>
            {product.name}
          </h3>
          <div className="flex items-center justify-between">
            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{inr(product.price)}</span>
            <button onClick={handleAdd} disabled={out} aria-label={`Add ${product.name} to cart`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium transition-colors hover:text-white hover:bg-[var(--accent)] disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ background: 'var(--btn-bg)', border: '1px solid var(--border)' }}>
              <ShoppingCart size={14} /> Add
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
}

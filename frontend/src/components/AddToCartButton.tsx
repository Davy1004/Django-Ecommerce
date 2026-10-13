'use client';
import { useState } from 'react';
import { Product } from '@/lib/api';
import { useCart } from '@/context/CartContext';
import { useToast } from '@/context/ToastContext';
import { Minus, Plus, ShoppingCart, Check } from 'lucide-react';
import Link from 'next/link';

export default function AddToCartButton({ product }: { product: Product }) {
  const { addItem } = useCart();
  const { show } = useToast();
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);
  const max = Math.min(product.stock, 10);

  if (product.stock === 0) {
    return <button disabled className="btn-primary w-full" style={{ padding: '14px 28px' }}>Out of stock</button>;
  }

  const add = () => {
    addItem({ id: product.id, name: product.name, price: product.price, image: product.image, slug: product.slug, stock: product.stock }, qty);
    show(`${qty} × ${product.name} added to cart`);
    setAdded(true);
    setTimeout(() => setAdded(false), 1800);
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-3">
        <div className="flex items-center rounded-xl" style={{ border: '1px solid var(--border)', background: 'var(--card-bg)' }}>
          <button aria-label="Decrease quantity" onClick={() => setQty(q => Math.max(1, q - 1))} className="w-11 h-12 flex items-center justify-center hover:opacity-60"><Minus size={16} /></button>
          <span aria-live="polite" style={{ minWidth: 28, textAlign: 'center', fontWeight: 600 }}>{qty}</span>
          <button aria-label="Increase quantity" onClick={() => setQty(q => Math.min(max, q + 1))} className="w-11 h-12 flex items-center justify-center hover:opacity-60"><Plus size={16} /></button>
        </div>
        <button onClick={add} className="btn-primary flex-1 flex items-center justify-center gap-2" style={{ padding: '14px 28px', fontSize: '1rem' }}>
          {added ? <Check size={18} /> : <ShoppingCart size={18} />}
          {added ? 'Added!' : 'Add to cart'}
        </button>
      </div>
      <Link href="/cart" className="text-sm text-center muted hover:opacity-70">View cart</Link>
    </div>
  );
}

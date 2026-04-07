'use client';
import Link from 'next/link';
import Image from 'next/image';
import { useCart } from '@/context/CartContext';
import { Product } from '@/lib/api';
import { ShoppingCart, Tag } from 'lucide-react';
import { useState } from 'react';

export default function ProductCard({ product }: { product: Product }) {
  const { addItem } = useCart();
  const [added, setAdded] = useState(false);

  const handleAdd = (e: React.MouseEvent) => {
    e.preventDefault();
    addItem({ id: product.id, name: product.name, price: product.price, image: product.image, slug: product.slug });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <Link href={`/products/${product.slug}`} className="group block" style={{ textDecoration: 'none' }}>
      <div className="rounded-2xl overflow-hidden transition-all duration-300 group-hover:-translate-y-1"
        style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', boxShadow: 'var(--card-shadow)' }}>
        <div className="relative overflow-hidden" style={{ height: '220px', background: 'var(--card-img-bg)' }}>
          {product.image ? (
            <Image src={product.image} alt={product.name} fill className="object-cover transition-transform duration-500 group-hover:scale-105" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Tag size={40} style={{ color: 'var(--fg-muted)', opacity: 0.3 }} />
            </div>
          )}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.4), transparent)' }} />
        </div>

        <div className="p-4">
          <p style={{ color: 'var(--accent)', fontSize: '0.72rem', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
            {product.category.name}
          </p>
          <h3 style={{ color: 'var(--fg)', fontFamily: 'var(--font-display)', fontSize: '1.05rem', lineHeight: 1.3 }}
            className="mb-3 line-clamp-2">{product.name}</h3>
          <div className="flex items-center justify-between">
            <span style={{ color: 'var(--fg)', fontWeight: 700, fontSize: '1.1rem' }}>
              ₹{product.price.toFixed(2)}
            </span>
            <button onClick={handleAdd}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium transition-all duration-200"
              style={{
                background: added ? 'var(--accent)' : 'var(--btn-bg)',
                color: added ? '#fff' : 'var(--fg)',
                border: '1px solid var(--border)',
              }}>
              <ShoppingCart size={14} />
              {added ? 'Added!' : 'Add'}
            </button>
          </div>
          {product.stock === 0 && (
            <p style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '6px' }}>Out of stock</p>
          )}
        </div>
      </div>
    </Link>
  );
}

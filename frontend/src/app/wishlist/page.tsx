'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Heart } from 'lucide-react';
import { getWishlist, Product } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useWishlist } from '@/context/WishlistContext';
import ProductCard from '@/components/ProductCard';

export default function WishlistPage() {
  const { user, loading: authLoading } = useAuth();
  const { ids } = useWishlist();
  const [items, setItems] = useState<Product[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) getWishlist().then(w => setItems(w.results)).catch(e => setError(e.message));
  }, [user]);

  // hearts toggled on this page disappear from the grid straight away
  const shown = items?.filter(p => ids.has(p.id));

  if (authLoading) return <div className="container-x py-12"><div className="skeleton" style={{ height: 240 }} /></div>;
  if (!user) {
    return (
      <div className="text-center px-6 py-24">
        <Heart size={48} className="muted" style={{ margin: '0 auto 16px', opacity: 0.4 }} />
        <p className="muted mb-6">Sign in to see the products you&apos;ve saved.</p>
        <Link href="/auth/login" className="btn-primary inline-block">Sign in</Link>
      </div>
    );
  }

  return (
    <div className="container-x py-10">
      <p className="eyebrow mb-2">Saved for later</p>
      <h1 className="section-title mb-8" style={{ fontSize: '2.3rem' }}>Your wishlist</h1>
      {error && <p className="card p-4 mb-6" style={{ color: '#dc2626' }}>{error}</p>}
      {!shown && !error && <div className="grid-products">{[0, 1, 2, 3].map(i => <div key={i} className="skeleton" style={{ aspectRatio: '1/1.25' }} />)}</div>}
      {shown && shown.length === 0 && (
        <div className="card text-center py-16 px-6">
          <Heart size={44} className="muted" style={{ margin: '0 auto 16px', opacity: 0.35 }} />
          <p className="muted mb-6">Nothing saved yet. Tap the heart on any product to keep it here.</p>
          <Link href="/products" className="btn-primary inline-block">Browse products</Link>
        </div>
      )}
      {shown && shown.length > 0 && <div className="grid-products">{shown.map(p => <ProductCard key={p.id} product={p} />)}</div>}
    </div>
  );
}

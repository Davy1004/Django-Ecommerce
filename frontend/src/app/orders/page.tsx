'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ReceiptText, ChevronRight } from 'lucide-react';
import { getOrders, OrderDetail } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { inr } from '@/lib/format';
import { StatusBadge, Thumb, fmtDate } from '@/components/OrderBits';

export default function OrdersPage() {
  const { user, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState<OrderDetail[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) return;
    getOrders().then(setOrders).catch(e => setError(e.message));
  }, [user]);

  if (authLoading) return <div className="container-x py-12"><div className="skeleton" style={{ height: 200 }} /></div>;
  if (!user) {
    return (
      <div className="text-center px-6 py-24">
        <ReceiptText size={48} className="muted" style={{ margin: '0 auto 16px', opacity: 0.4 }} />
        <p className="muted mb-6">Sign in to see your orders.</p>
        <Link href="/auth/login" className="btn-primary inline-block">Sign in</Link>
      </div>
    );
  }

  return (
    <div className="container-x py-10" style={{ maxWidth: '56rem' }}>
      <p className="eyebrow mb-2">Account</p>
      <h1 className="section-title mb-8" style={{ fontSize: '2.3rem' }}>Your orders</h1>

      {error && <p className="card p-4 mb-6" style={{ color: '#dc2626' }}>{error}</p>}
      {!orders && !error && <div className="flex flex-col gap-4">{[0, 1, 2].map(i => <div key={i} className="skeleton" style={{ height: 110 }} />)}</div>}

      {orders && orders.length === 0 && (
        <div className="card text-center py-16 px-6">
          <ReceiptText size={44} className="muted" style={{ margin: '0 auto 16px', opacity: 0.35 }} />
          <p className="muted mb-6">You haven&apos;t placed any orders yet.</p>
          <Link href="/products" className="btn-primary inline-block">Start shopping</Link>
        </div>
      )}

      <div className="flex flex-col gap-4">
        {orders?.map(o => (
          <Link key={o.id} href={`/orders/${o.id}`} className="card p-5 flex items-center gap-5 hover:-translate-y-0.5 transition-transform">
            <div className="hidden sm:flex -space-x-3">
              {o.items.slice(0, 3).map(i => <span key={i.product_id} className="rounded-xl" style={{ border: '2px solid var(--card-bg)' }}><Thumb name={i.product_name} size={52} /></span>)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap mb-1">
                <span style={{ fontWeight: 700 }}>Order #{o.id}</span><StatusBadge status={o.status} />
              </div>
              <p className="muted text-sm line-clamp-1">{o.items.map(i => `${i.product_name} × ${i.quantity}`).join(', ')}</p>
              <p className="muted text-xs mt-1">{fmtDate(o.created_at)}</p>
            </div>
            <div className="text-right"><p style={{ fontWeight: 700, fontSize: '1.05rem' }}>{inr(o.total_amount)}</p></div>
            <ChevronRight size={18} className="muted" />
          </Link>
        ))}
      </div>
    </div>
  );
}

'use client';
import { use, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Loader2, MapPin, Mail, Phone } from 'lucide-react';
import { cancelOrder, getOrder, OrderDetail, payOrder } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { inr } from '@/lib/format';
import Breadcrumbs from '@/components/Breadcrumbs';
import { StatusBadge, Thumb, fmtDate } from '@/components/OrderBits';

export default function OrderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user, loading: authLoading } = useAuth();
  const { show } = useToast();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<'pay' | 'cancel' | null>(null);

  const load = useCallback(() => getOrder(id).then(setOrder).catch(e => setError(e.message)), [id]);
  useEffect(() => { if (user) load(); }, [user, load]);

  const act = async (kind: 'pay' | 'cancel') => {
    setBusy(kind);
    try {
      if (kind === 'pay') await payOrder(Number(id), `mock_pay_${id}`, 'mock_success');
      else await cancelOrder(Number(id));
      show(kind === 'pay' ? 'Payment received, thank you!' : 'Order cancelled');
      await load();
    } catch (e) {
      show(e instanceof Error ? e.message : 'Something went wrong', 'error');
    } finally {
      setBusy(null);
    }
  };

  if (authLoading) return <div className="container-x py-12"><div className="skeleton" style={{ height: 300 }} /></div>;
  if (!user) return <div className="text-center px-6 py-24"><p className="muted mb-6">Sign in to view this order.</p><Link href="/auth/login" className="btn-primary inline-block">Sign in</Link></div>;
  if (error) return <div className="text-center px-6 py-24"><p className="muted mb-6">{error === 'API Error: 404' || /not found/i.test(error) ? 'We couldn’t find that order.' : error}</p><Link href="/orders" className="btn-ghost">All orders</Link></div>;
  if (!order) return <div className="container-x py-12"><div className="skeleton" style={{ height: 300 }} /></div>;

  return (
    <div className="container-x py-10" style={{ maxWidth: '56rem' }}>
      <Breadcrumbs trail={[{ label: 'Home', href: '/' }, { label: 'Orders', href: '/orders' }, { label: `Order #${order.id}` }]} />
      <div className="flex items-center justify-between flex-wrap gap-4 mb-8">
        <div>
          <h1 className="section-title" style={{ fontSize: '2.1rem' }}>Order #{order.id}</h1>
          <p className="muted text-sm mt-1">Placed on {fmtDate(order.created_at)}</p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      {order.status === 'PENDING' && (
        <div className="card p-5 mb-6 flex items-center justify-between gap-4 flex-wrap" style={{ background: '#fffbeb', borderColor: '#fde68a' }}>
          <p className="text-sm" style={{ color: '#92400e' }}>This order is waiting for payment. Your items are reserved for a short while.</p>
          <div className="flex gap-3">
            <button onClick={() => act('pay')} disabled={!!busy} className="btn-primary flex items-center gap-2" style={{ padding: '10px 20px' }}>
              {busy === 'pay' && <Loader2 size={16} className="animate-spin" />} Pay {inr(order.total_amount)}
            </button>
            <button onClick={() => act('cancel')} disabled={!!busy} className="btn-ghost" style={{ padding: '10px 20px' }}>
              {busy === 'cancel' && <Loader2 size={16} className="animate-spin" />} Cancel
            </button>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6">
        <div className="card md:col-span-2 p-6">
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: 18 }}>Items</h2>
          <div className="flex flex-col gap-4">
            {order.items.map(i => (
              <div key={i.product_id + i.product_name} className="flex items-center gap-4">
                <Thumb name={i.product_name} size={60} />
                <div className="flex-1 min-w-0">
                  <p className="line-clamp-1" style={{ fontWeight: 600 }}>{i.product_name}</p>
                  <p className="muted text-sm">{inr(i.unit_price)} × {i.quantity}</p>
                </div>
                <span style={{ fontWeight: 600 }}>{inr(i.line_total)}</span>
              </div>
            ))}
          </div>
          <div className="flex justify-between pt-5 mt-5 font-bold" style={{ borderTop: '1px solid var(--border)', fontSize: '1.1rem' }}>
            <span>Total</span><span>{inr(order.total_amount)}</span>
          </div>
        </div>

        <div className="card p-6 h-fit">
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: 16 }}>Delivery</h2>
          <div className="flex flex-col gap-3 text-sm">
            <p style={{ fontWeight: 600 }}>{order.name}</p>
            <p className="flex gap-2 muted"><MapPin size={16} className="shrink-0 mt-0.5" /> {order.address}, {order.city}</p>
            <p className="flex gap-2 muted"><Mail size={16} className="shrink-0 mt-0.5" /> {order.email}</p>
            <p className="flex gap-2 muted"><Phone size={16} className="shrink-0 mt-0.5" /> {order.phone}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

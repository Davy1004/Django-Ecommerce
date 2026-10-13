'use client';
import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, ArrowRight } from 'lucide-react';
import { getOrder, OrderDetail } from '@/lib/api';
import { inr } from '@/lib/format';
import { Thumb } from '@/components/OrderBits';

function Success() {
  const id = useSearchParams().get('order');
  const [order, setOrder] = useState<OrderDetail | null>(null);
  useEffect(() => { if (id) getOrder(id).then(setOrder).catch(() => setOrder(null)); }, [id]);

  return (
    <div className="max-w-xl mx-auto px-6 py-20 text-center">
      <CheckCircle size={72} style={{ color: '#22c55e', margin: '0 auto 24px' }} />
      <h1 className="section-title" style={{ fontSize: '2.4rem', marginBottom: 14 }}>Thank you for your order!</h1>
      <p className="muted" style={{ lineHeight: 1.7, marginBottom: 32 }}>
        {order ? <>Order <strong>#{order.id}</strong> is confirmed and being packed.</> : 'Your order is confirmed and being packed.'} A confirmation is on its way to your email.
      </p>

      {order && (
        <div className="card p-5 mb-8 text-left">
          {order.items.map(i => (
            <div key={i.product_id} className="flex items-center gap-3 py-2">
              <Thumb name={i.product_name} size={44} />
              <span className="flex-1 line-clamp-1 text-sm">{i.product_name} <span className="muted">× {i.quantity}</span></span>
              <span className="text-sm" style={{ fontWeight: 600 }}>{inr(i.line_total)}</span>
            </div>
          ))}
          <div className="flex justify-between pt-3 mt-2 font-bold" style={{ borderTop: '1px solid var(--border)' }}><span>Total paid</span><span>{inr(order.total_amount)}</span></div>
        </div>
      )}

      <div className="flex gap-3 justify-center flex-wrap">
        {id && <Link href={`/orders/${id}`} className="btn-ghost">View order</Link>}
        <Link href="/products" className="btn-primary inline-flex items-center gap-2">Continue shopping <ArrowRight size={16} /></Link>
      </div>
    </div>
  );
}

export default function OrderSuccessPage() {
  return <Suspense><Success /></Suspense>;
}

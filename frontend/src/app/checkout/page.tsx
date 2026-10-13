'use client';
import { useState } from 'react';
import { useCart } from '@/context/CartContext';
import { placeOrder, payOrder, previewCoupon, CouponQuote } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2, Lock, Tag, X } from 'lucide-react';
import { inr } from '@/lib/format';
import { useToast } from '@/context/ToastContext';

export default function CheckoutPage() {
  const { items, totalPrice, clearCart } = useCart();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const { show } = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [code, setCode] = useState('');
  const [quote, setQuote] = useState<CouponQuote | null>(null);
  const [couponMsg, setCouponMsg] = useState('');
  const [checking, setChecking] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', address: '', city: '', phone: '' });

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  if (!authLoading && !user) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-24 text-center">
        <p style={{ color: 'var(--fg-muted)', marginBottom: '24px' }}>Please sign in to place an order.</p>
        <Link href="/auth/login" className="btn-primary inline-block">Sign in</Link>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-24 text-center">
        <p style={{ color: 'var(--fg-muted)', marginBottom: '24px' }}>Your cart is empty.</p>
        <Link href="/products" className="btn-primary inline-block">Shop Now</Link>
      </div>
    );
  }

  const cartLines = items.map(i => ({ product_id: i.id, quantity: i.quantity }));
  const payable = quote ? quote.total : totalPrice;

  const applyCoupon = async () => {
    if (!code.trim()) return;
    setChecking(true); setCouponMsg('');
    try { setQuote(await previewCoupon(code.trim(), cartLines)); }
    catch (err) { setQuote(null); setCouponMsg(err instanceof Error ? err.message : 'Could not apply that coupon'); }
    finally { setChecking(false); }
  };
  const removeCoupon = () => { setQuote(null); setCode(''); setCouponMsg(''); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    let orderId: number | null = null;
    try {
      // One key per checkout attempt: a double click or retry can't create two orders.
      const key = crypto.randomUUID();
      const order = await placeOrder(
        { ...form, items: cartLines, coupon_code: quote?.code ?? '' },
        key,
      );
      orderId = order.id;
      // Demo payment (PAYMENT_PROVIDER=mock). With Razorpay you would open Razorpay Checkout
      // using order.payment.key_id / provider_order_id, then send its payment_id + signature here.
      await payOrder(order.id, `mock_pay_${order.id}`, 'mock_success');
      clearCart();
      router.push(`/order-success?order=${order.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      if (orderId !== null) {
        // The order exists (stock is reserved) but payment failed: send them to it so they can retry or cancel.
        clearCart();
        show('Order created, but payment did not go through', 'error');
        router.push(`/orders/${orderId}`);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <Link href="/cart" className="inline-flex items-center gap-2 mb-10 hover:opacity-70 transition-opacity"
        style={{ color: 'var(--fg-muted)', fontSize: '0.9rem' }}>
        <ArrowLeft size={16} /> Back to cart
      </Link>

      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', marginBottom: '36px' }}>Checkout</h1>

      <div className="grid md:grid-cols-5 gap-10">
        {/* Form */}
        <form onSubmit={handleSubmit} className="md:col-span-3 flex flex-col gap-5">
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '4px' }}>Shipping Details</h2>

          {error && (
            <div className="p-4 rounded-xl text-sm" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626' }}>
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Full Name</label>
              <input value={form.name} onChange={set('name')} required placeholder="John Doe" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Email Address</label>
              <input type="email" value={form.email} onChange={set('email')} required placeholder="john@example.com" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Address</label>
              <textarea value={form.address} onChange={set('address')} required placeholder="123 Main Street"
                style={{ minHeight: '80px', resize: 'none' }} />
            </div>
            <div>
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>City</label>
              <input value={form.city} onChange={set('city')} required placeholder="Mumbai" />
            </div>
            <div>
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Phone</label>
              <input type="tel" value={form.phone} onChange={set('phone')} required placeholder="+91 98765 43210" />
            </div>
          </div>

          <p className="text-xs muted flex items-center gap-1.5"><Lock size={12} /> Demo checkout: your card is never charged.</p>
          <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center gap-2 mt-1">
            {loading ? <><Loader2 size={18} className="animate-spin" /> Placing Order...</> : `Place order — ${inr(payable)}`}
          </button>
        </form>

        {/* Order Summary */}
        <div className="md:col-span-2">
          <div className="rounded-2xl p-6" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '20px' }}>Your Order</h2>
            <div className="flex flex-col gap-4 mb-6">
              {items.map(item => (
                <div key={item.id} className="flex gap-3 items-center">
                  <div className="relative rounded-lg overflow-hidden flex-shrink-0"
                    style={{ width: 48, height: 48, background: 'var(--card-img-bg)' }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={item.image || `/products/${item.slug}.svg`} alt={item.name} className="w-full h-full object-cover" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p style={{ fontSize: '0.85rem', color: 'var(--fg)' }} className="line-clamp-1">{item.name}</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--fg-muted)' }}>×{item.quantity}</p>
                  </div>
                  <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{inr(item.price * item.quantity)}</span>
                </div>
              ))}
            </div>
            <div className="mb-5">
              {quote ? (
                <div className="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-sm" style={{ background: '#dcfce7', color: '#166534' }}>
                  <span className="flex items-center gap-2"><Tag size={15} /> <strong>{quote.code}</strong> applied</span>
                  <button type="button" onClick={removeCoupon} aria-label="Remove coupon"><X size={16} /></button>
                </div>
              ) : (
                <>
                  <div className="flex gap-2">
                    <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} placeholder="Coupon code" aria-label="Coupon code"
                      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); applyCoupon(); } }} style={{ padding: '10px 14px' }} />
                    <button type="button" onClick={applyCoupon} disabled={checking || !code.trim()} className="btn-ghost" style={{ padding: '10px 16px' }}>
                      {checking ? <Loader2 size={15} className="animate-spin" /> : 'Apply'}
                    </button>
                  </div>
                  {couponMsg ? <p className="text-xs mt-2" style={{ color: '#dc2626' }}>{couponMsg}</p>
                    : <p className="text-xs mt-2 muted">Try <button type="button" className="underline" onClick={() => setCode('WELCOME10')}>WELCOME10</button> or <button type="button" className="underline" onClick={() => setCode('FLAT200')}>FLAT200</button></p>}
                </>
              )}
            </div>
            <div className="border-t pt-4 flex flex-col gap-2" style={{ borderColor: 'var(--border)' }}>
              <div className="flex justify-between text-sm muted"><span>Subtotal</span><span>{inr(totalPrice)}</span></div>
              {quote && <div className="flex justify-between text-sm" style={{ color: '#16a34a' }}><span>Discount ({quote.code})</span><span>-{inr(quote.discount)}</span></div>}
              <div className="flex justify-between font-bold text-lg pt-1"><span>Total</span><span>{inr(payable)}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

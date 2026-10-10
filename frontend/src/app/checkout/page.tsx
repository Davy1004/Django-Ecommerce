'use client';
import { useState } from 'react';
import { useCart } from '@/context/CartContext';
import { placeOrder, payOrder } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';

export default function CheckoutPage() {
  const { items, totalPrice, clearCart } = useCart();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // One key per checkout attempt: a double click or retry can't create two orders.
      const key = crypto.randomUUID();
      const order = await placeOrder(
        { ...form, items: items.map(i => ({ product_id: i.id, quantity: i.quantity })) },
        key,
      );
      // Demo payment (PAYMENT_PROVIDER=mock). With Razorpay you would open Razorpay Checkout
      // using order.payment.key_id / provider_order_id, then send its payment_id + signature here.
      await payOrder(order.id, `mock_pay_${order.id}`, 'mock_success');
      clearCart();
      router.push('/order-success');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
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

          <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center gap-2 mt-2">
            {loading ? <><Loader2 size={18} className="animate-spin" /> Placing Order...</> : `Place Order — ₹${totalPrice.toFixed(2)}`}
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
                    {item.image && <Image src={item.image} alt={item.name} fill className="object-cover" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p style={{ fontSize: '0.85rem', color: 'var(--fg)' }} className="line-clamp-1">{item.name}</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--fg-muted)' }}>×{item.quantity}</p>
                  </div>
                  <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>₹{(item.price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="border-t pt-4" style={{ borderColor: 'var(--border)' }}>
              <div className="flex justify-between font-bold">
                <span>Total</span>
                <span>₹{totalPrice.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

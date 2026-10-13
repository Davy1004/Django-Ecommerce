'use client';
import { useCart } from '@/context/CartContext';
import Link from 'next/link';
import { Minus, Plus, Trash2, ShoppingBag, ArrowRight } from 'lucide-react';
import { inr } from '@/lib/format';

export default function CartPage() {
  const { items, removeItem, updateQuantity, clearCart, totalPrice, totalItems } = useCart();

  if (items.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-24 text-center">
        <ShoppingBag size={64} style={{ color: 'var(--fg-muted)', opacity: 0.2, margin: '0 auto 24px' }} />
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', marginBottom: '12px' }}>Your cart is empty</h1>
        <p style={{ color: 'var(--fg-muted)', marginBottom: '32px' }}>Looks like you haven&apos;t added anything yet.</p>
        <Link href="/products" className="btn-primary inline-flex items-center gap-2">
          Start Shopping <ArrowRight size={16} />
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="flex items-end justify-between mb-8">
        <h1 className="section-title" style={{ fontSize: '2.2rem' }}>Your cart <span className="muted" style={{ fontSize: '1rem', fontFamily: 'var(--font-body)' }}>({totalItems} item{totalItems !== 1 ? 's' : ''})</span></h1>
        <button onClick={clearCart} className="text-sm muted hover:text-[#dc2626] transition-colors">Clear cart</button>
      </div>

      <div className="grid md:grid-cols-3 gap-10">
        {/* Items */}
        <div className="md:col-span-2 flex flex-col gap-4">
          {items.map(item => (
            <div key={item.id} className="flex gap-4 p-4 rounded-2xl"
              style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
              <div className="relative rounded-xl overflow-hidden flex-shrink-0"
                style={{ width: 88, height: 88, background: 'var(--card-img-bg)' }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={item.image || `/products/${item.slug}.svg`} alt={item.name} className="w-full h-full object-cover" />
              </div>
              <div className="flex-1 min-w-0">
                <Link href={`/products/${item.slug}`}
                  style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', color: 'var(--fg)' }}
                  className="hover:opacity-70 transition-opacity line-clamp-2">
                  {item.name}
                </Link>
                <p style={{ color: 'var(--accent)', fontWeight: 700, marginTop: '4px' }}>
                  {inr(item.price * item.quantity)}
                </p>
              </div>
              <div className="flex flex-col items-end gap-3">
                <button onClick={() => removeItem(item.id)} className="hover:opacity-60 transition-opacity">
                  <Trash2 size={16} style={{ color: 'var(--fg-muted)' }} />
                </button>
                <div className="flex items-center gap-2">
                  <button onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors hover:bg-[var(--border)]"
                    style={{ border: '1px solid var(--border)' }}>
                    <Minus size={12} />
                  </button>
                  <span style={{ fontWeight: 600, minWidth: '20px', textAlign: 'center' }}>{item.quantity}</span>
                  <button onClick={() => updateQuantity(item.id, item.quantity + 1)} disabled={item.stock !== undefined && item.quantity >= item.stock}
                    aria-label="Increase quantity"
                    className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors hover:bg-[var(--border)] disabled:opacity-30"
                    style={{ border: '1px solid var(--border)' }}>
                    <Plus size={12} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="h-fit rounded-2xl p-6" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', marginBottom: '20px' }}>Order Summary</h2>
          <div className="flex justify-between mb-3" style={{ color: 'var(--fg-muted)', fontSize: '0.9rem' }}>
            <span>Subtotal ({totalItems} items)</span>
            <span>{inr(totalPrice)}</span>
          </div>
          <div className="flex justify-between mb-3" style={{ color: 'var(--fg-muted)', fontSize: '0.9rem' }}>
            <span>Shipping</span>
            <span style={{ color: '#22c55e' }}>Free</span>
          </div>
          <div className="border-t pt-4 mt-4 flex justify-between font-bold" style={{ borderColor: 'var(--border)', fontSize: '1.1rem' }}>
            <span>Total</span>
            <span>{inr(totalPrice)}</span>
          </div>
          <Link href="/checkout" className="btn-primary flex items-center justify-center gap-2 mt-6 w-full">
            Proceed to Checkout <ArrowRight size={16} />
          </Link>
          <Link href="/products" className="block text-center mt-4 text-sm hover:opacity-70 transition-opacity"
            style={{ color: 'var(--fg-muted)' }}>
            Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
}

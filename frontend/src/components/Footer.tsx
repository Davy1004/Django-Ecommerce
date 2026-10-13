import Link from 'next/link';
import { Package } from 'lucide-react';

export default function Footer() {
  const link = 'hover:text-[var(--accent)] transition-colors';
  return (
    <footer className="mt-24" style={{ background: '#1a1208', color: '#d9cdb8' }}>
      <div className="container-x py-14 grid gap-10 md:grid-cols-4">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Package size={22} style={{ color: 'var(--accent)' }} />
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', color: '#fff' }}>shopcraft</span>
          </div>
          <p style={{ maxWidth: 380, lineHeight: 1.7, fontSize: '0.92rem' }}>
            A demo store built with Django REST Framework and Next.js. Orders, stock locking and the payment-event pipeline are real; the payments are simulated, so nothing is ever charged.
          </p>
        </div>
        <div>
          <h4 style={{ color: '#fff', marginBottom: 14, fontWeight: 600 }}>Shop</h4>
          <ul className="flex flex-col gap-2.5 text-sm" style={{ listStyle: 'none' }}>
            <li><Link href="/products" className={link}>All products</Link></li>
            <li><Link href="/categories" className={link}>Categories</Link></li>
            <li><Link href="/cart" className={link}>Your cart</Link></li>
          </ul>
        </div>
        <div>
          <h4 style={{ color: '#fff', marginBottom: 14, fontWeight: 600 }}>Account</h4>
          <ul className="flex flex-col gap-2.5 text-sm" style={{ listStyle: 'none' }}>
            <li><Link href="/auth/login" className={link}>Sign in</Link></li>
            <li><Link href="/auth/register" className={link}>Create account</Link></li>
            <li><Link href="/orders" className={link}>Your orders</Link></li>
          </ul>
        </div>
      </div>
      <div style={{ borderTop: '1px solid #ffffff1a' }}>
        <div className="container-x py-5 text-xs flex justify-between flex-wrap gap-2" style={{ color: '#9c8f78' }}>
          <span>© {new Date().getFullYear()} ShopCraft demo store</span>
          <span>Illustrations drawn in code · no real payments</span>
        </div>
      </div>
    </footer>
  );
}

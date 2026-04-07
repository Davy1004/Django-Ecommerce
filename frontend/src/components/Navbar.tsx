'use client';
import Link from 'next/link';
import { useCart } from '@/context/CartContext';
import { useAuth } from '@/context/AuthContext';
import { ShoppingCart, User, LogOut, Package } from 'lucide-react';

export default function Navbar() {
  const { totalItems } = useCart();
  const { user, logout } = useAuth();

  return (
    <nav style={{ background: 'var(--nav-bg)', borderBottom: '1px solid var(--border)' }}
      className="sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Package size={22} style={{ color: 'var(--accent)' }} />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', color: 'var(--fg)', letterSpacing: '-0.02em' }}>
            shopcraft
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link href="/products" style={{ color: 'var(--fg-muted)', fontSize: '0.9rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}
            className="hover:opacity-70 transition-opacity">Products</Link>
          <Link href="/categories" style={{ color: 'var(--fg-muted)', fontSize: '0.9rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}
            className="hover:opacity-70 transition-opacity">Categories</Link>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/cart" className="relative group">
            <ShoppingCart size={22} style={{ color: 'var(--fg)' }} className="group-hover:opacity-70 transition-opacity" />
            {totalItems > 0 && (
              <span className="absolute -top-2 -right-2 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold"
                style={{ background: 'var(--accent)', fontSize: '0.65rem' }}>
                {totalItems}
              </span>
            )}
          </Link>
          {user ? (
            <div className="flex items-center gap-3">
              <span style={{ color: 'var(--fg-muted)', fontSize: '0.85rem' }}>{user.username}</span>
              <button onClick={logout} className="hover:opacity-70 transition-opacity">
                <LogOut size={18} style={{ color: 'var(--fg-muted)' }} />
              </button>
            </div>
          ) : (
            <Link href="/auth/login" className="hover:opacity-70 transition-opacity">
              <User size={22} style={{ color: 'var(--fg)' }} />
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCart } from '@/context/CartContext';
import { useAuth } from '@/context/AuthContext';
import { ShoppingCart, User, LogOut, Package, Search, Menu, X, ReceiptText, Heart, LayoutDashboard } from 'lucide-react';
import { useWishlist } from '@/context/WishlistContext';

export default function Navbar() {
  const { totalItems } = useCart();
  const { user, logout } = useAuth();
  const { count: wishCount } = useWishlist();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');

  const search = (e: React.FormEvent) => {
    e.preventDefault();
    setOpen(false);
    router.push(q.trim() ? `/products?search=${encodeURIComponent(q.trim())}` : '/products');
  };
  const nav = 'text-sm font-medium hover:text-[var(--accent)] transition-colors';

  return (
    <header className="sticky top-0 z-50">
      <div className="text-center text-xs py-2 px-4" style={{ background: '#1a1208', color: '#f3e8d2' }}>
        Free delivery on every order · Demo store, payments are simulated
      </div>
      <nav style={{ background: 'var(--nav-bg)', backdropFilter: 'blur(10px)', borderBottom: '1px solid var(--border)' }}>
        <div className="container-x py-3.5 flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <Package size={22} style={{ color: 'var(--accent)' }} />
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', letterSpacing: '-0.02em' }}>shopcraft</span>
          </Link>

          <div className="hidden md:flex items-center gap-7">
            <Link href="/products" className={nav}>Products</Link>
            <Link href="/categories" className={nav}>Categories</Link>
            {user && <Link href="/orders" className={nav}>Orders</Link>}
            {user?.is_staff && <Link href="/dashboard" className={`${nav} flex items-center gap-1.5`}><LayoutDashboard size={15} /> Dashboard</Link>}
          </div>

          <form onSubmit={search} role="search" className="hidden md:flex flex-1 max-w-md ml-auto relative">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 muted" />
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search products…" aria-label="Search products"
              style={{ paddingLeft: 38, paddingTop: 9, paddingBottom: 9, borderRadius: 999 }} />
          </form>

          <div className="flex items-center gap-4 ml-auto md:ml-0">
            <Link href="/wishlist" className="relative group hidden sm:block" aria-label={`Wishlist, ${wishCount} items`}>
              <Heart size={22} className="group-hover:opacity-70 transition-opacity" />
              {wishCount > 0 && (
                <span className="absolute -top-2 -right-2 text-white rounded-full w-5 h-5 flex items-center justify-center font-bold"
                  style={{ background: '#e11d48', fontSize: '0.65rem' }}>{wishCount}</span>
              )}
            </Link>
            <Link href="/cart" className="relative group" aria-label={`Cart, ${totalItems} items`}>
              <ShoppingCart size={22} className="group-hover:opacity-70 transition-opacity" />
              {totalItems > 0 && (
                <span className="absolute -top-2 -right-2 text-white rounded-full w-5 h-5 flex items-center justify-center font-bold"
                  style={{ background: 'var(--accent)', fontSize: '0.65rem' }}>{totalItems}</span>
              )}
            </Link>
            {user ? (
              <div className="hidden md:flex items-center gap-3">
                <span className="muted text-sm">{user.username}</span>
                <button onClick={logout} aria-label="Sign out" className="hover:opacity-70"><LogOut size={18} className="muted" /></button>
              </div>
            ) : (
              <Link href="/auth/login" aria-label="Sign in" className="hidden md:block hover:opacity-70"><User size={22} /></Link>
            )}
            <button className="md:hidden" onClick={() => setOpen(o => !o)} aria-label="Menu" aria-expanded={open}>
              {open ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {open && (
          <div className="md:hidden container-x pb-5 flex flex-col gap-4">
            <form onSubmit={search} role="search" className="relative">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 muted" />
              <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search products…" aria-label="Search products" style={{ paddingLeft: 38, borderRadius: 999 }} />
            </form>
            <Link href="/products" onClick={() => setOpen(false)} className={nav}>Products</Link>
            <Link href="/categories" onClick={() => setOpen(false)} className={nav}>Categories</Link>
            <Link href="/wishlist" onClick={() => setOpen(false)} className={`${nav} flex items-center gap-2`}><Heart size={16} /> Wishlist {wishCount > 0 && `(${wishCount})`}</Link>
            {user?.is_staff && <Link href="/dashboard" onClick={() => setOpen(false)} className={`${nav} flex items-center gap-2`}><LayoutDashboard size={16} /> Dashboard</Link>}
            {user ? (
              <>
                <Link href="/orders" onClick={() => setOpen(false)} className={`${nav} flex items-center gap-2`}><ReceiptText size={16} /> Your orders</Link>
                <button onClick={() => { setOpen(false); logout(); }} className={`${nav} text-left flex items-center gap-2`}><LogOut size={16} /> Sign out ({user.username})</button>
              </>
            ) : (
              <Link href="/auth/login" onClick={() => setOpen(false)} className={nav}>Sign in</Link>
            )}
          </div>
        )}
      </nav>
    </header>
  );
}

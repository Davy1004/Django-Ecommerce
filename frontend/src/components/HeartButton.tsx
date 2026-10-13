'use client';
import { Heart } from 'lucide-react';
import { useWishlist } from '@/context/WishlistContext';

export default function HeartButton({ productId, name, className = '', size = 18 }: { productId: number; name?: string; className?: string; size?: number }) {
  const { has, toggle } = useWishlist();
  const on = has(productId);
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={on ? `Remove ${name ?? 'item'} from wishlist` : `Save ${name ?? 'item'} to wishlist`}
      onClick={e => { e.preventDefault(); e.stopPropagation(); toggle(productId, name); }}
      className={`flex items-center justify-center rounded-full transition-transform hover:scale-110 active:scale-95 ${className}`}
      style={{ background: 'rgba(255,255,255,.92)', width: size + 18, height: size + 18, boxShadow: '0 1px 4px rgba(0,0,0,.15)' }}>
      <Heart size={size} fill={on ? '#e11d48' : 'none'} style={{ color: on ? '#e11d48' : '#6b5c45' }} />
    </button>
  );
}

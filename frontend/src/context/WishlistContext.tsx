'use client';
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { addToWishlist, getWishlist, removeFromWishlist } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';

interface WishlistContextType {
  ids: Set<number>;
  count: number;
  has: (id: number) => boolean;
  toggle: (id: number, name?: string) => Promise<void>;
}

const WishlistContext = createContext<WishlistContextType | null>(null);

export function WishlistProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const { show } = useToast();
  const [ids, setIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!user) { setIds(new Set()); return; }
    getWishlist().then(w => setIds(new Set(w.results.map(p => p.id)))).catch(() => {});
  }, [user]);

  const toggle = useCallback(async (id: number, name?: string) => {
    if (!user) { show('Sign in to save items to your wishlist', 'error'); return; }
    const had = ids.has(id);
    // optimistic: flip the heart immediately, undo if the server says no
    setIds(prev => { const n = new Set(prev); had ? n.delete(id) : n.add(id); return n; });
    try {
      await (had ? removeFromWishlist(id) : addToWishlist(id));
      show(had ? `Removed${name ? ` ${name}` : ''} from wishlist` : `Saved${name ? ` ${name}` : ''} to wishlist`);
    } catch {
      setIds(prev => { const n = new Set(prev); had ? n.add(id) : n.delete(id); return n; });
      show('Could not update your wishlist', 'error');
    }
  }, [user, ids, show]);

  return (
    <WishlistContext.Provider value={{ ids, count: ids.size, has: id => ids.has(id), toggle }}>
      {children}
    </WishlistContext.Provider>
  );
}

export function useWishlist() {
  const ctx = useContext(WishlistContext);
  if (!ctx) throw new Error('useWishlist must be used within WishlistProvider');
  return ctx;
}

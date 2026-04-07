'use client';
import { useCart } from '@/context/CartContext';
import { Product } from '@/lib/api';
import { ShoppingCart, Check } from 'lucide-react';
import { useState } from 'react';

export default function AddToCartButton({ product }: { product: Product }) {
  const { addItem } = useCart();
  const [added, setAdded] = useState(false);

  const handle = () => {
    addItem({ id: product.id, name: product.name, price: product.price, image: product.image, slug: product.slug });
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  return (
    <button onClick={handle} disabled={product.stock === 0}
      className="btn-primary flex items-center gap-2 w-full justify-center"
      style={{ padding: '14px 28px', fontSize: '1rem', opacity: product.stock === 0 ? 0.5 : 1 }}>
      {added ? <Check size={18} /> : <ShoppingCart size={18} />}
      {added ? 'Added to Cart!' : product.stock === 0 ? 'Out of Stock' : 'Add to Cart'}
    </button>
  );
}

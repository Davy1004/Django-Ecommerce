import { getProduct, getProducts } from '@/lib/api';
import AddToCartButton from '@/components/AddToCartButton';
import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Package } from 'lucide-react';

export async function generateStaticParams() {
  const products = await getProducts().catch(() => []);
  return products.map(p => ({ slug: p.slug }));
}

// Next 15+/16: route params arrive as a Promise and must be awaited.
export default async function ProductDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = await getProduct(slug).catch(() => null);
  if (!product) notFound();

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <Link href="/products" className="inline-flex items-center gap-2 mb-10 hover:opacity-70 transition-opacity"
        style={{ color: 'var(--fg-muted)', fontSize: '0.9rem' }}>
        <ArrowLeft size={16} /> Back to products
      </Link>

      <div className="grid md:grid-cols-2 gap-16 items-start">
        {/* Image */}
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--card-img-bg)', aspectRatio: '1', position: 'relative' }}>
          {product.image ? (
            <Image src={product.image} alt={product.name} fill className="object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Package size={80} style={{ color: 'var(--fg-muted)', opacity: 0.2 }} />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="py-4">
          <Link href={`/categories/${product.category.slug}`}
            style={{ color: 'var(--accent)', fontSize: '0.8rem', letterSpacing: '0.12em', textTransform: 'uppercase' }}
            className="hover:opacity-70 transition-opacity">
            {product.category.name}
          </Link>

          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.8rem, 4vw, 2.6rem)', lineHeight: 1.2, marginTop: '12px', marginBottom: '20px' }}>
            {product.name}
          </h1>

          <div className="flex items-baseline gap-3 mb-6">
            <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--fg)' }}>
              ₹{product.price.toFixed(2)}
            </span>
            <span style={{ fontSize: '0.85rem', color: product.stock > 0 ? '#22c55e' : '#ef4444', fontWeight: 500 }}>
              {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
            </span>
          </div>

          <p style={{ color: 'var(--fg-muted)', lineHeight: 1.8, fontSize: '1rem', marginBottom: '32px' }}>
            {product.description}
          </p>

          <AddToCartButton product={product} />
        </div>
      </div>
    </div>
  );
}

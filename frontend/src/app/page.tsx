import { getProducts, getCategories } from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

export default async function HomePage() {
  const [products, categories] = await Promise.all([
    getProducts().catch(() => []),
    getCategories().catch(() => []),
  ]);

  const featured = products.slice(0, 8);

  return (
    <div>
      {/* Hero */}
      <section className="px-6 py-24 max-w-7xl mx-auto">
        <div className="max-w-2xl">
          <p style={{ color: 'var(--accent)', fontSize: '0.8rem', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '16px' }}>
            Curated Collection
          </p>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(2.5rem, 6vw, 4.5rem)', lineHeight: 1.1, color: 'var(--fg)', marginBottom: '24px' }}>
            Crafted for those<br />who appreciate quality
          </h1>
          <p style={{ color: 'var(--fg-muted)', fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '36px', maxWidth: '480px' }}>
            Discover our handpicked selection of premium products. Each item chosen for its craftsmanship and lasting value.
          </p>
          <div className="flex gap-4 flex-wrap">
            <Link href="/products" className="btn-primary flex items-center gap-2">
              Shop Now <ArrowRight size={16} />
            </Link>
            <Link href="/categories"
              style={{ padding: '12px 24px', border: '1px solid var(--border)', borderRadius: '12px', color: 'var(--fg)', fontSize: '0.95rem', fontWeight: 500, transition: 'background 0.2s' }}
              className="hover:bg-[var(--btn-bg)]">
              Browse Categories
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section className="px-6 py-12 max-w-7xl mx-auto">
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', marginBottom: '20px' }}>Shop by Category</h2>
          <div className="flex gap-3 flex-wrap">
            {categories.map(cat => (
              <Link key={cat.id} href={`/categories/${cat.slug}`}
                className="px-5 py-2.5 rounded-full text-sm font-medium transition-all hover:scale-105"
                style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', color: 'var(--fg)' }}>
                {cat.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="px-6 py-12 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem' }}>Featured Products</h2>
          <Link href="/products" className="flex items-center gap-1 text-sm hover:opacity-70 transition-opacity"
            style={{ color: 'var(--accent)' }}>
            View all <ArrowRight size={14} />
          </Link>
        </div>
        {featured.length === 0 ? (
          <div className="text-center py-20" style={{ color: 'var(--fg-muted)' }}>
            <p>No products yet. Add some from the Django admin!</p>
          </div>
        ) : (
          <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
            {featured.map(p => <ProductCard key={p.id} product={p} />)}
          </div>
        )}
      </section>
    </div>
  );
}

import { getProducts, getCategories } from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import Link from 'next/link';

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: { category?: string; search?: string };
}) {
  const [products, categories] = await Promise.all([
    getProducts({ category: searchParams.category, search: searchParams.search }).catch(() => []),
    getCategories().catch(() => []),
  ]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', marginBottom: '8px' }}>
        All Products
      </h1>
      <p style={{ color: 'var(--fg-muted)', marginBottom: '32px' }}>
        {products.length} item{products.length !== 1 ? 's' : ''} found
      </p>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap mb-10">
        <Link href="/products"
          className="px-4 py-2 rounded-full text-sm font-medium transition-all"
          style={{
            background: !searchParams.category ? 'var(--accent)' : 'var(--card-bg)',
            color: !searchParams.category ? '#fff' : 'var(--fg)',
            border: '1px solid var(--border)',
          }}>
          All
        </Link>
        {categories.map(cat => (
          <Link key={cat.id} href={`/products?category=${cat.slug}`}
            className="px-4 py-2 rounded-full text-sm font-medium transition-all"
            style={{
              background: searchParams.category === cat.slug ? 'var(--accent)' : 'var(--card-bg)',
              color: searchParams.category === cat.slug ? '#fff' : 'var(--fg)',
              border: '1px solid var(--border)',
            }}>
            {cat.name}
          </Link>
        ))}
      </div>

      {products.length === 0 ? (
        <div className="text-center py-24" style={{ color: 'var(--fg-muted)' }}>
          <p className="text-xl mb-3">No products found</p>
          <Link href="/products" style={{ color: 'var(--accent)' }}>Clear filters</Link>
        </div>
      ) : (
        <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
          {products.map(p => <ProductCard key={p.id} product={p} />)}
        </div>
      )}
    </div>
  );
}

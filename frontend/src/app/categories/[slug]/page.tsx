import { getCategoryWithProducts, getCategories, getProducts } from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';

export async function generateStaticParams() {
  const cats = await getCategories().catch(() => []);
  return cats.map(c => ({ slug: c.slug }));
}

// Next 15+/16: route params arrive as a Promise and must be awaited.
export default async function CategoryDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const category = await getCategoryWithProducts(slug).catch(() => null);
  if (!category) notFound();

  // Fetch full product data
  const products = await getProducts({ category: slug }).catch(() => []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <Link href="/categories" className="inline-flex items-center gap-2 mb-10 hover:opacity-70 transition-opacity"
        style={{ color: 'var(--fg-muted)', fontSize: '0.9rem' }}>
        <ArrowLeft size={16} /> All categories
      </Link>

      <div className="mb-10">
        <p style={{ color: 'var(--accent)', fontSize: '0.8rem', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '8px' }}>
          Collection
        </p>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.4rem' }}>{category.name}</h1>
        <p style={{ color: 'var(--fg-muted)', marginTop: '8px' }}>{products.length} products</p>
      </div>

      {products.length === 0 ? (
        <div className="text-center py-20" style={{ color: 'var(--fg-muted)' }}>No products in this category yet.</div>
      ) : (
        <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
          {products.map(p => <ProductCard key={p.id} product={p} />)}
        </div>
      )}
    </div>
  );
}

import { getCategories } from '@/lib/api';
import Link from 'next/link';
import { ArrowRight, Grid } from 'lucide-react';

export default async function CategoriesPage() {
  const categories = await getCategories().catch(() => []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', marginBottom: '8px' }}>Categories</h1>
      <p style={{ color: 'var(--fg-muted)', marginBottom: '40px' }}>Browse our curated collections</p>

      {categories.length === 0 ? (
        <div className="text-center py-24" style={{ color: 'var(--fg-muted)' }}>
          <Grid size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
          <p>No categories yet.</p>
        </div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          {categories.map(cat => (
            <Link key={cat.id} href={`/categories/${cat.slug}`}
              className="group flex items-center justify-between p-6 rounded-2xl transition-all hover:-translate-y-0.5"
              style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', boxShadow: 'var(--card-shadow)' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', color: 'var(--fg)' }}>
                {cat.name}
              </span>
              <ArrowRight size={18} style={{ color: 'var(--accent)' }} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

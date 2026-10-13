import Link from 'next/link';
import type { Metadata } from 'next';
import { ArrowRight } from 'lucide-react';
import { getCategories, getProducts, safe } from '@/lib/api';
import { categoryImage } from '@/lib/format';
import ApiDown from '@/components/ApiDown';

export const dynamic = 'force-dynamic';
export const metadata: Metadata = { title: 'Categories' };

export default async function CategoriesPage() {
  const [categories, products] = await Promise.all([safe(getCategories()), safe(getProducts())]);
  if (!categories || !products) return <ApiDown />;
  const counts = products.reduce<Record<string, number>>((m, p) => ((m[p.category.slug] = (m[p.category.slug] ?? 0) + 1), m), {});

  return (
    <div className="container-x py-10">
      <p className="eyebrow mb-2">Collections</p>
      <h1 className="section-title" style={{ fontSize: '2.3rem' }}>Shop by category</h1>
      <p className="muted mt-2 mb-10">Pick a collection and start browsing.</p>
      <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
        {categories.map(c => (
          <Link key={c.id} href={`/categories/${c.slug}`} className="tile card overflow-hidden block group">
            <div className="overflow-hidden" style={{ aspectRatio: '16 / 10' }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={categoryImage(c.slug)} alt="" className="tile-img w-full h-full object-cover" />
            </div>
            <div className="p-5 flex items-center justify-between">
              <div>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem' }}>{c.name}</h2>
                <p className="muted text-sm">{counts[c.slug] ?? 0} products</p>
              </div>
              <ArrowRight size={20} style={{ color: 'var(--accent)' }} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

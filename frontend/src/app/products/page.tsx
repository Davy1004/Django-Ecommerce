import Link from 'next/link';
import type { Metadata } from 'next';
import { Search, X } from 'lucide-react';
import { getProductsPage, getCategories, safe, PAGE_SIZE } from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import SortSelect from '@/components/SortSelect';
import Pagination from '@/components/Pagination';
import ApiDown from '@/components/ApiDown';

export const dynamic = 'force-dynamic';
export const metadata: Metadata = { title: 'All products' };

type SP = { category?: string; search?: string; ordering?: string; page?: string };

export default async function ProductsPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const page = Math.max(1, parseInt(sp.page ?? '1', 10) || 1);
  const [data, categories] = await Promise.all([
    safe(getProductsPage({ category: sp.category, search: sp.search, ordering: sp.ordering, page })),
    safe(getCategories()),
  ]);
  if (!data || !categories) return <ApiDown />;

  const pages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));
  const keep = { search: sp.search, ordering: sp.ordering };
  const build = (o: Record<string, string | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(o).forEach(([k, v]) => v && qs.set(k, v));
    return `/products${qs.size ? '?' + qs : ''}`;
  };
  const href = (cat?: string) => build({ ...keep, category: cat });
  const clearSearch = build({ ordering: sp.ordering, category: sp.category });
  const active = categories.find(c => c.slug === sp.category);

  return (
    <div className="container-x py-10">
      <div className="mb-8">
        <p className="eyebrow mb-2">Catalogue</p>
        <h1 className="section-title" style={{ fontSize: '2.3rem' }}>{active ? active.name : 'All products'}</h1>
        <p className="muted mt-2">{data.count} item{data.count !== 1 ? 's' : ''}{sp.search ? <> matching <strong>&ldquo;{sp.search}&rdquo;</strong></> : ' available'}</p>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
          <Link href={href()} className={`chip ${!sp.category ? 'chip-active' : ''}`}>All</Link>
          {categories.map(c => <Link key={c.id} href={href(c.slug)} className={`chip ${sp.category === c.slug ? 'chip-active' : ''}`}>{c.name}</Link>)}
        </div>
        <div className="flex items-center gap-4 shrink-0">
          {sp.search && <Link href={clearSearch} className="chip flex items-center gap-1.5"><X size={13} /> Clear search</Link>}
          <SortSelect basePath="/products" />
        </div>
      </div>

      {data.results.length === 0 ? (
        <div className="card text-center py-20 px-6">
          <Search size={44} className="muted" style={{ margin: '0 auto 16px', opacity: 0.35 }} />
          <h2 className="section-title" style={{ fontSize: '1.4rem', marginBottom: 8 }}>No products found</h2>
          <p className="muted" style={{ marginBottom: 22 }}>Try a different search word or remove a filter.</p>
          <Link href="/products" className="btn-primary inline-block">Clear all filters</Link>
        </div>
      ) : (
        <div className="grid-products">{data.results.map(p => <ProductCard key={p.id} product={p} />)}</div>
      )}

      <Pagination page={page} pages={pages} basePath="/products" params={{ ...keep, category: sp.category }} />
    </div>
  );
}

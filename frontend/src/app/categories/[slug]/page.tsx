import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ApiError, getCategories, getProductsPage, safe, PAGE_SIZE } from '@/lib/api';
import { categoryImage } from '@/lib/format';
import ProductCard from '@/components/ProductCard';
import SortSelect from '@/components/SortSelect';
import Pagination from '@/components/Pagination';
import Breadcrumbs from '@/components/Breadcrumbs';
import ApiDown from '@/components/ApiDown';

export const dynamic = 'force-dynamic';

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ ordering?: string; page?: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = (await params).slug;
  const cat = (await safe(getCategories()))?.find(c => c.slug === slug);
  return { title: cat?.name ?? 'Category' };
}

export default async function CategoryDetailPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const sp = await searchParams;
  const page = Math.max(1, parseInt(sp.page ?? '1', 10) || 1);

  const [categories, data] = await Promise.all([safe(getCategories()), safe(getProductsPage({ category: slug, ordering: sp.ordering, page }))]);
  if (!categories || !data) return <ApiDown />;
  const category = categories.find(c => c.slug === slug);
  if (!category) notFound();
  const others = categories.filter(c => c.slug !== slug);
  const pages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));

  return (
    <div className="container-x py-10">
      <Breadcrumbs trail={[{ label: 'Home', href: '/' }, { label: 'Categories', href: '/categories' }, { label: category.name }]} />

      <div className="card overflow-hidden grid md:grid-cols-[1fr_320px] items-center mb-10">
        <div className="p-8 md:p-10">
          <p className="eyebrow mb-2">Collection</p>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.6rem', lineHeight: 1.1 }}>{category.name}</h1>
          <p className="muted mt-3">{data.count} product{data.count !== 1 ? 's' : ''}</p>
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={categoryImage(slug)} alt="" className="hidden md:block w-full h-full object-cover" style={{ maxHeight: 200 }} />
      </div>

      <div className="flex items-center justify-between gap-4 flex-wrap mb-8">
        <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
          {others.map(c => <Link key={c.id} href={`/categories/${c.slug}`} className="chip">{c.name}</Link>)}
        </div>
        <SortSelect basePath={`/categories/${slug}`} />
      </div>

      {data.results.length === 0
        ? <div className="card text-center py-16 muted">No products in this category yet.</div>
        : <div className="grid-products">{data.results.map(p => <ProductCard key={p.id} product={p} />)}</div>}

      <Pagination page={page} pages={pages} basePath={`/categories/${slug}`} params={{ ordering: sp.ordering }} />
    </div>
  );
}

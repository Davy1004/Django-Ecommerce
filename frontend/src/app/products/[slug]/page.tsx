import { cache } from 'react';
import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { Truck, ShieldCheck, RotateCcw } from 'lucide-react';
import { ApiError, getProduct, getProductsPage, safe } from '@/lib/api';
import { inr, productImage, stockLabel } from '@/lib/format';
import AddToCartButton from '@/components/AddToCartButton';
import ProductCard from '@/components/ProductCard';
import Breadcrumbs from '@/components/Breadcrumbs';
import ApiDown from '@/components/ApiDown';

export const dynamic = 'force-dynamic';

// one fetch shared by generateMetadata and the page
const load = cache(async (slug: string) => {
  try {
    return { product: await getProduct(slug), missing: false };
  } catch (e) {
    return { product: null, missing: e instanceof ApiError && e.status === 404 };
  }
});

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { product } = await load((await params).slug);
  return product ? { title: product.name, description: product.description.slice(0, 160) } : { title: 'Product' };
}

export default async function ProductDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const { product, missing } = await load(slug);
  if (missing) notFound();
  if (!product) return <ApiDown what="this product" />;

  const related = (await safe(getProductsPage({ category: product.category.slug, pageSize: 5 })))?.results.filter(p => p.id !== product.id).slice(0, 4) ?? [];
  const low = product.stock > 0 && product.stock <= 5;

  return (
    <div className="container-x py-10">
      <Breadcrumbs trail={[{ label: 'Home', href: '/' }, { label: 'Products', href: '/products' }, { label: product.category.name, href: `/categories/${product.category.slug}` }, { label: product.name }]} />

      <div className="grid md:grid-cols-2 gap-10 lg:gap-16 items-start">
        <div className="card overflow-hidden md:sticky md:top-28" style={{ aspectRatio: '1 / 1', background: 'var(--card-img-bg)' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={productImage(product)} alt={product.name} className="w-full h-full object-cover" />
        </div>

        <div>
          <Link href={`/categories/${product.category.slug}`} className="eyebrow hover:opacity-70">{product.category.name}</Link>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.9rem, 4vw, 2.7rem)', lineHeight: 1.15, margin: '10px 0 18px' }}>{product.name}</h1>

          <div className="flex items-center gap-4 mb-6 flex-wrap">
            <span style={{ fontSize: '2.1rem', fontWeight: 700 }}>{inr(product.price)}</span>
            <span className={`badge ${product.stock === 0 ? 'badge-cancelled' : low ? 'badge-pending' : 'badge-paid'}`}>{stockLabel(product)}</span>
          </div>
          <p className="muted" style={{ fontSize: '0.8rem', marginTop: -12, marginBottom: 20 }}>Inclusive of all taxes · Free delivery</p>

          <p className="muted" style={{ lineHeight: 1.85, fontSize: '1.02rem', marginBottom: 28 }}>{product.description}</p>

          <AddToCartButton product={product} />

          <ul className="card mt-8 p-5 flex flex-col gap-4 text-sm" style={{ listStyle: 'none' }}>
            <li className="flex items-center gap-3"><Truck size={18} style={{ color: 'var(--accent)' }} /> Free delivery, dispatched within 24 hours</li>
            <li className="flex items-center gap-3"><RotateCcw size={18} style={{ color: 'var(--accent)' }} /> 7-day easy returns</li>
            <li className="flex items-center gap-3"><ShieldCheck size={18} style={{ color: 'var(--accent)' }} /> Secure checkout with stock reserved at purchase</li>
          </ul>

          <dl className="mt-6 text-sm grid grid-cols-[120px_1fr] gap-y-2.5">
            <dt className="muted">Category</dt><dd>{product.category.name}</dd>
            <dt className="muted">Product code</dt><dd>SC-{String(product.id).padStart(5, '0')}</dd>
            <dt className="muted">Availability</dt><dd>{stockLabel(product)}</dd>
          </dl>
        </div>
      </div>

      {related.length > 0 && (
        <section className="mt-24">
          <h2 className="section-title mb-7">You might also like</h2>
          <div className="grid-products">{related.map(p => <ProductCard key={p.id} product={p} />)}</div>
        </section>
      )}
    </div>
  );
}

import Link from 'next/link';
import { ArrowRight, Truck, ShieldCheck, RotateCcw, Headphones, Sparkles } from 'lucide-react';
import { getProducts, getCategories, safe, Product } from '@/lib/api';
import { categoryImage, productImage } from '@/lib/format';
import ProductCard from '@/components/ProductCard';
import ApiDown from '@/components/ApiDown';

export const dynamic = 'force-dynamic'; // always read the live catalogue; never bake an empty page at build time

const FEATURED = ['smart-watch', 'wireless-earbuds', 'running-sneakers', 'mechanical-keyboard', 'led-desk-lamp', 'canvas-backpack', 'yoga-mat', 'clean-code'];
const HERO = ['smart-watch', 'running-sneakers', 'led-desk-lamp', 'wireless-earbuds'];

const PERKS = [
  { icon: Truck, title: 'Free delivery', text: 'On every order, no minimum' },
  { icon: ShieldCheck, title: 'Safe payments', text: 'Signed, idempotent checkout' },
  { icon: RotateCcw, title: '7-day returns', text: 'Changed your mind? No fuss' },
  { icon: Headphones, title: 'Friendly support', text: 'We reply within a day' },
];

export default async function HomePage() {
  const [products, categories] = await Promise.all([safe(getProducts()), safe(getCategories())]);
  if (!products || !categories) return <ApiDown />;

  const bySlug = new Map(products.map(p => [p.slug, p]));
  const featured = FEATURED.map(s => bySlug.get(s)).filter((p): p is Product => !!p);
  const featuredList = featured.length >= 4 ? featured : products.slice(0, 8);
  const taken = new Set(featuredList.map(p => p.id));
  const fresh = products.filter(p => !taken.has(p.id)).slice(0, 4);
  const heroItems = HERO.map(s => bySlug.get(s)).filter((p): p is Product => !!p);
  const counts = products.reduce<Record<string, number>>((m, p) => ((m[p.category.slug] = (m[p.category.slug] ?? 0) + 1), m), {});

  return (
    <div>
      {/* Hero */}
      <section className="container-x pt-14 pb-16 grid md:grid-cols-2 gap-12 items-center">
        <div className="fade-up">
          <p className="eyebrow mb-4 flex items-center gap-2"><Sparkles size={14} /> New season, new picks</p>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(2.4rem, 5.5vw, 4.2rem)', lineHeight: 1.08, marginBottom: 22 }}>
            Everyday things,<br />chosen with care.
          </h1>
          <p className="muted" style={{ fontSize: '1.1rem', lineHeight: 1.7, marginBottom: 32, maxWidth: 470 }}>
            Gadgets, books, home goods and gear for work and life. {products.length} products across {categories.length} collections, all in stock and ready to ship.
          </p>
          <div className="flex gap-4 flex-wrap">
            <Link href="/products" className="btn-primary inline-flex items-center gap-2">Shop now <ArrowRight size={16} /></Link>
            <Link href="/categories" className="btn-ghost">Browse categories</Link>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 fade-up" style={{ animationDelay: '0.1s' }}>
          {heroItems.map((p, i) => (
            <Link key={p.id} href={`/products/${p.slug}`} className="tile card overflow-hidden relative block"
              style={{ aspectRatio: '1 / 1', transform: `translateY(${i % 2 ? 22 : 0}px)` }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={productImage(p)} alt={p.name} className="tile-img w-full h-full object-cover" />
              <span className="absolute bottom-3 left-3 badge" style={{ background: 'rgba(255,255,255,.92)' }}>{p.name}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Perks */}
      <section style={{ background: 'var(--card-bg)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div className="container-x py-7 grid grid-cols-2 md:grid-cols-4 gap-6">
          {PERKS.map(({ icon: Icon, title, text }) => (
            <div key={title} className="flex items-center gap-3">
              <span className="flex items-center justify-center rounded-full shrink-0" style={{ width: 44, height: 44, background: 'var(--btn-bg)' }}>
                <Icon size={20} style={{ color: 'var(--accent)' }} />
              </span>
              <div><p style={{ fontWeight: 600, fontSize: '0.92rem' }}>{title}</p><p className="muted" style={{ fontSize: '0.8rem' }}>{text}</p></div>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="container-x pt-16">
        <div className="flex items-end justify-between mb-7">
          <div><p className="eyebrow mb-2">Collections</p><h2 className="section-title">Shop by category</h2></div>
          <Link href="/categories" className="hidden sm:flex items-center gap-1 text-sm hover:opacity-70" style={{ color: 'var(--accent)' }}>All categories <ArrowRight size={14} /></Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {categories.map(c => (
            <Link key={c.id} href={`/categories/${c.slug}`} className="tile card overflow-hidden block">
              <div className="overflow-hidden" style={{ aspectRatio: '1 / 1' }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={categoryImage(c.slug)} alt="" className="tile-img w-full h-full object-cover" />
              </div>
              <div className="p-3.5">
                <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem' }}>{c.name}</p>
                <p className="muted" style={{ fontSize: '0.78rem' }}>{counts[c.slug] ?? 0} products</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured */}
      <section className="container-x pt-20">
        <div className="flex items-end justify-between mb-7">
          <div><p className="eyebrow mb-2">Customer favourites</p><h2 className="section-title">Featured products</h2></div>
          <Link href="/products" className="flex items-center gap-1 text-sm hover:opacity-70" style={{ color: 'var(--accent)' }}>View all <ArrowRight size={14} /></Link>
        </div>
        <div className="grid-products">{featuredList.map(p => <ProductCard key={p.id} product={p} />)}</div>
      </section>

      {/* Promo */}
      <section className="container-x pt-20">
        <div className="rounded-3xl overflow-hidden grid md:grid-cols-2 items-center" style={{ background: 'linear-gradient(120deg, #1a1208, #3d2008)', color: '#fff' }}>
          <div className="p-10 md:p-14">
            <p className="eyebrow mb-3">Reading list</p>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.8rem, 3.5vw, 2.6rem)', lineHeight: 1.15, marginBottom: 14 }}>Books for people who build things</h2>
            <p style={{ color: '#d9cdb8', lineHeight: 1.7, marginBottom: 26 }}>From clean code to distributed systems and classic algorithms: the shelf every developer ends up needing.</p>
            <Link href="/categories/books" className="btn-primary inline-flex items-center gap-2">Browse books <ArrowRight size={16} /></Link>
          </div>
          <div className="hidden md:grid grid-cols-3 gap-3 p-8">
            {['clean-code', 'designing-data-intensive-applications', 'introduction-to-algorithms'].map((s, i) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={s} src={`/products/${s}.svg`} alt="" className="rounded-2xl w-full" style={{ aspectRatio: '1/1', objectFit: 'cover', transform: `translateY(${i === 1 ? 18 : 0}px)` }} />
            ))}
          </div>
        </div>
      </section>

      {/* More */}
      {fresh.length > 0 && (
        <section className="container-x pt-20">
          <div className="mb-7"><p className="eyebrow mb-2">Just in</p><h2 className="section-title">More to explore</h2></div>
          <div className="grid-products">{fresh.map(p => <ProductCard key={p.id} product={p} />)}</div>
        </section>
      )}
    </div>
  );
}

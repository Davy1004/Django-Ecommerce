'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, IndianRupee, Loader2, Package, Receipt, ShieldAlert, Tag, TrendingUp, Users } from 'lucide-react';
import { getSalesDashboard, SalesDashboard } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { inr } from '@/lib/format';
import RevenueChart from '@/components/RevenueChart';
import { StatusBadge, fmtDate } from '@/components/OrderBits';

const RANGES = [7, 30, 90] as const;

function Kpi({ icon: Icon, label, value, hint }: { icon: typeof Package; label: string; value: string; hint?: string }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3"><span className="muted text-sm">{label}</span><Icon size={18} style={{ color: 'var(--accent)' }} /></div>
      <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.9rem', lineHeight: 1.1 }}>{value}</p>
      {hint && <p className="muted text-xs mt-1.5">{hint}</p>}
    </div>
  );
}

function Bars({ rows }: { rows: { label: string; value: number; note: string }[] }) {
  const max = Math.max(1, ...rows.map(r => r.value));
  if (!rows.length) return <p className="muted text-sm">Nothing sold in this period yet.</p>;
  return (
    <ul className="flex flex-col gap-3.5" style={{ listStyle: 'none' }}>
      {rows.map(r => (
        <li key={r.label}>
          <div className="flex justify-between text-sm mb-1.5 gap-3"><span className="truncate">{r.label}</span><span className="muted shrink-0">{r.note}</span></div>
          <div className="rounded-full overflow-hidden" style={{ height: 8, background: 'var(--btn-bg)' }}>
            <div style={{ width: `${(r.value / max) * 100}%`, height: '100%', background: 'var(--accent)', borderRadius: 999 }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [days, setDays] = useState<number>(30);
  const [data, setData] = useState<SalesDashboard | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user?.is_staff) return;
    setError('');
    getSalesDashboard(days).then(setData).catch(e => setError(e.message));
  }, [user, days]);

  if (authLoading) return <div className="container-x py-12"><div className="skeleton" style={{ height: 300 }} /></div>;
  if (!user || !user.is_staff) {
    return (
      <div className="text-center px-6 py-24">
        <ShieldAlert size={48} className="muted" style={{ margin: '0 auto 16px', opacity: 0.4 }} />
        <h1 className="section-title mb-2" style={{ fontSize: '1.6rem' }}>Staff only</h1>
        <p className="muted mb-6">{user ? 'Your account does not have access to the sales dashboard.' : 'Sign in with a staff account to see sales.'}</p>
        <Link href={user ? '/' : '/auth/login'} className="btn-primary inline-block">{user ? 'Back to shop' : 'Sign in'}</Link>
      </div>
    );
  }

  const t = data?.totals;
  return (
    <div className="container-x py-10">
      <div className="flex items-end justify-between gap-4 flex-wrap mb-8">
        <div><p className="eyebrow mb-2">Admin</p><h1 className="section-title" style={{ fontSize: '2.3rem' }}>Sales dashboard</h1></div>
        <div className="flex gap-2" role="group" aria-label="Date range">
          {RANGES.map(r => <button key={r} onClick={() => setDays(r)} className={`chip ${days === r ? 'chip-active' : ''}`}>Last {r} days</button>)}
        </div>
      </div>

      {error && <p className="card p-4 mb-6" style={{ color: '#dc2626' }}>{error}</p>}
      {!data && !error && <div className="flex items-center gap-2 muted"><Loader2 className="animate-spin" size={18} /> Loading numbers…</div>}

      {data && t && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <Kpi icon={IndianRupee} label={`Revenue (${days}d)`} value={inr(data.range.revenue)} hint={`${inr(t.revenue)} all time`} />
            <Kpi icon={Receipt} label={`Paid orders (${days}d)`} value={String(data.range.orders)} hint={`${t.paid_orders} all time`} />
            <Kpi icon={TrendingUp} label="Avg order value" value={inr(Math.round(t.average_order_value))} />
            <Kpi icon={Package} label="Units sold" value={String(t.units_sold)} />
            <Kpi icon={Users} label="Customers" value={String(t.customers)} hint="with a paid order" />
            <Kpi icon={Tag} label="Discounts given" value={inr(t.discounts_given)} />
          </div>

          <div className="card p-6">
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 14 }}>Revenue per day</h2>
            <RevenueChart data={data.daily} />
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="card p-6">
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 18 }}>Top products</h2>
              <Bars rows={data.top_products.map(p => ({ label: p.name, value: p.revenue, note: `${inr(p.revenue)} · ${p.units} sold` }))} />
            </div>
            <div className="card p-6">
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 18 }}>Revenue by category</h2>
              <Bars rows={data.by_category.map(c => ({ label: c.category, value: c.revenue, note: `${inr(c.revenue)} · ${c.units} unit${c.units !== 1 ? 's' : ''}` }))} />
            </div>
            <div className="card p-6">
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 18 }}>Orders by status</h2>
              <div className="flex flex-col gap-3 mb-6">
                {(['PAID', 'PENDING', 'CANCELLED'] as const).map(s => (
                  <div key={s} className="flex items-center justify-between"><StatusBadge status={s} /><strong>{t.orders_by_status[s]}</strong></div>
                ))}
              </div>
              <h3 className="text-sm muted mb-2">Coupons ({days}d)</h3>
              {data.coupons.length === 0 ? <p className="muted text-sm">No coupon orders yet.</p> : (
                <ul className="flex flex-col gap-2 text-sm" style={{ listStyle: 'none' }}>
                  {data.coupons.map(c => <li key={c.code} className="flex justify-between"><strong>{c.code}</strong><span className="muted">{c.orders} order{c.orders > 1 ? 's' : ''} · -{inr(c.discount)}</span></li>)}
                </ul>
              )}
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="card p-6 lg:col-span-2">
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 14 }}>Recent orders</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm" style={{ borderCollapse: 'collapse', minWidth: 460 }}>
                  <thead><tr className="muted text-left"><th className="py-2 font-medium">Order</th><th className="font-medium">Customer</th><th className="font-medium">Date</th><th className="font-medium">Status</th><th className="font-medium text-right">Total</th></tr></thead>
                  <tbody>
                    {data.recent_orders.map(o => (
                      <tr key={o.id} style={{ borderTop: '1px solid var(--border)' }}>
                        <td className="py-2.5 font-semibold">#{o.id}</td><td>{o.customer}</td><td className="muted">{fmtDate(o.created_at)}</td>
                        <td><StatusBadge status={o.status} /></td><td className="text-right font-semibold">{inr(o.total)}</td>
                      </tr>
                    ))}
                    {data.recent_orders.length === 0 && <tr><td colSpan={5} className="py-6 text-center muted">No orders yet.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card p-6">
              <h2 className="flex items-center gap-2" style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 14 }}><AlertTriangle size={18} style={{ color: '#d97706' }} /> Low stock</h2>
              {data.low_stock.length === 0 ? <p className="muted text-sm">Everything is well stocked.</p> : (
                <ul className="flex flex-col gap-3 text-sm" style={{ listStyle: 'none' }}>
                  {data.low_stock.map(p => (
                    <li key={p.id} className="flex justify-between gap-3"><Link href={`/products/${p.slug}`} className="truncate hover:text-[var(--accent)]">{p.name}</Link>
                      <span className={`badge ${p.stock === 0 ? 'badge-cancelled' : 'badge-pending'}`}>{p.stock === 0 ? 'Sold out' : `${p.stock} left`}</span></li>
                  ))}
                </ul>
              )}
              <p className="muted text-xs mt-6">{data.catalogue.products} products · {data.catalogue.reviews} reviews{data.catalogue.average_rating ? ` (avg ${data.catalogue.average_rating})` : ''} · {data.catalogue.coupons_active} active coupons</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

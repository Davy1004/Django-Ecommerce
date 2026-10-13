'use client';
import { useState } from 'react';
import { fmtDay, inr } from '@/lib/format';

type Point = { date: string; revenue: number; orders: number };

const niceMax = (v: number) => {
  if (v <= 0) return 100;
  const pow = 10 ** Math.floor(Math.log10(v));
  const n = v / pow;
  return ([1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find(x => n <= x) ?? 10) * pow;
};

/** Dependency-free SVG bar chart: one bar per day, hover/focus shows the exact numbers. */
export default function RevenueChart({ data }: { data: Point[] }) {
  const [active, setActive] = useState<number | null>(null);
  const W = 720, H = 240, L = 52, R = 8, T = 12, B = 28;
  const max = niceMax(Math.max(...data.map(d => d.revenue), 0));
  const bw = (W - L - R) / data.length;
  const y = (v: number) => T + (H - T - B) * (1 - v / max);
  const step = Math.ceil(data.length / 8);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => f * max);
  const hit = active !== null ? data[active] : null;
  const empty = data.every(d => d.revenue === 0);

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Revenue per day">
        {ticks.map(t => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="var(--border)" strokeDasharray={t ? '3 4' : undefined} />
            <text x={L - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--fg-muted)">{t >= 1000 ? `${+(t / 1000).toFixed(2)}k` : +t.toFixed(0)}</text>
          </g>
        ))}
        {data.map((d, i) => (
          <g key={d.date} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(i)} onBlur={() => setActive(null)} tabIndex={0}
            aria-label={`${fmtDay(d.date)}: ${inr(d.revenue)} from ${d.orders} orders`}>
            <rect x={L + i * bw} y={T} width={bw} height={H - T - B} fill="transparent" />
            <rect x={L + i * bw + bw * 0.15} y={y(d.revenue)} width={Math.max(bw * 0.7, 1)} height={Math.max(H - B - y(d.revenue), d.revenue > 0 ? 2 : 0)}
              rx={Math.min(3, bw * 0.3)} fill={active === i ? 'var(--accent-hover)' : 'var(--accent)'} opacity={active === null || active === i ? 1 : 0.55} />
            {i % step === 0 && <text x={L + i * bw + bw / 2} y={H - 8} textAnchor="middle" fontSize="11" fill="var(--fg-muted)">{fmtDay(d.date)}</text>}
          </g>
        ))}
      </svg>
      {empty && <p className="absolute inset-0 flex items-center justify-center text-sm muted pointer-events-none">No paid orders in this period yet</p>}
      {hit && (
        <div className="absolute top-1 right-2 card px-3 py-2 text-xs" style={{ pointerEvents: 'none' }}>
          <strong>{fmtDay(hit.date)}</strong><br />{inr(hit.revenue)} · {hit.orders} order{hit.orders !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}

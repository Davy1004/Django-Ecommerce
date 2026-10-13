import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function Pagination({ page, pages, basePath, params }: { page: number; pages: number; basePath: string; params: Record<string, string | undefined> }) {
  if (pages <= 1) return null;
  const href = (p: number) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v && qs.set(k, v));
    if (p > 1) qs.set('page', String(p));
    return `${basePath}${qs.size ? '?' + qs : ''}`;
  };
  const box = { width: 40, height: 40, borderRadius: 12, border: '1px solid var(--border)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.9rem' } as const;
  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-2 mt-12">
      {page > 1 && <Link href={href(page - 1)} aria-label="Previous page" style={box}><ChevronLeft size={16} /></Link>}
      {Array.from({ length: pages }, (_, i) => i + 1).map(p => (
        <Link key={p} href={href(p)} aria-current={p === page ? 'page' : undefined}
          style={{ ...box, background: p === page ? 'var(--accent)' : 'var(--card-bg)', color: p === page ? '#fff' : 'var(--fg)', borderColor: p === page ? 'var(--accent)' : 'var(--border)' }}>
          {p}
        </Link>
      ))}
      {page < pages && <Link href={href(page + 1)} aria-label="Next page" style={box}><ChevronRight size={16} /></Link>}
    </nav>
  );
}

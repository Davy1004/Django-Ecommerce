import Link from 'next/link';
import { ChevronRight } from 'lucide-react';

export default function Breadcrumbs({ trail }: { trail: { label: string; href?: string }[] }) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center flex-wrap gap-1.5 mb-8 text-sm muted">
      {trail.map((t, i) => (
        <span key={t.label} className="flex items-center gap-1.5">
          {t.href ? <Link href={t.href} className="hover:text-[var(--accent)] transition-colors">{t.label}</Link> : <span style={{ color: 'var(--fg)' }}>{t.label}</span>}
          {i < trail.length - 1 && <ChevronRight size={14} />}
        </span>
      ))}
    </nav>
  );
}

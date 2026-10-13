'use client';
import { useRouter, useSearchParams } from 'next/navigation';
import { SORTS } from '@/lib/format';

export default function SortSelect({ basePath }: { basePath: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const change = (value: string) => {
    const qs = new URLSearchParams(params.toString());
    qs.delete('page');
    value ? qs.set('ordering', value) : qs.delete('ordering');
    router.push(`${basePath}${qs.size ? '?' + qs : ''}`);
  };
  return (
    <label className="flex items-center gap-2 text-sm muted">
      Sort
      <select aria-label="Sort products" value={params.get('ordering') ?? ''} onChange={e => change(e.target.value)}
        style={{ width: 'auto', padding: '8px 12px', fontSize: '0.85rem' }}>
        {SORTS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
      </select>
    </label>
  );
}

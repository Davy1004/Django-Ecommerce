import { Star } from 'lucide-react';

/** Read-only star row; supports halves by overlaying a clipped filled star. */
export default function Stars({ value, size = 14 }: { value: number | null | undefined; size?: number }) {
  const v = value ?? 0;
  return (
    <span className="inline-flex items-center gap-0.5" role="img" aria-label={value ? `${value} out of 5 stars` : 'No ratings yet'}>
      {[1, 2, 3, 4, 5].map(i => {
        const fill = Math.max(0, Math.min(1, v - (i - 1)));
        return (
          <span key={i} className="relative inline-block" style={{ width: size, height: size }}>
            <Star size={size} style={{ color: '#d9cdb8' }} />
            {fill > 0 && (
              <span className="absolute inset-0 overflow-hidden" style={{ width: `${fill * 100}%` }}>
                <Star size={size} fill="#f59e0b" style={{ color: '#f59e0b' }} />
              </span>
            )}
          </span>
        );
      })}
    </span>
  );
}

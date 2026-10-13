'use client';
import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { BadgeCheck, Loader2, Star, Trash2 } from 'lucide-react';
import { deleteReview, getReviews, ReviewsPayload, saveReview } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { timeAgo } from '@/lib/format';
import Stars from '@/components/Stars';

export default function Reviews({ slug }: { slug: string }) {
  const { user, loading: authLoading } = useAuth();
  const { show } = useToast();
  const router = useRouter();
  const [data, setData] = useState<ReviewsPayload | null>(null);
  const [failed, setFailed] = useState(false);
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => getReviews(slug).then(setData).catch(() => setFailed(true)), [slug]);
  useEffect(() => { load(); }, [load, user]);

  const mine = data?.results.find(r => r.is_mine);
  useEffect(() => {
    if (mine) { setRating(mine.rating); setTitle(mine.title); setBody(mine.body); }
    else { setRating(0); setTitle(''); setBody(''); }
  }, [mine?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rating) { show('Pick a star rating first', 'error'); return; }
    setBusy(true);
    try {
      setData(await saveReview(slug, { rating, title: title.trim(), body: body.trim() }));
      show(mine ? 'Review updated' : 'Thanks for your review!');
      router.refresh(); // update the star line at the top of the page too
    } catch (err) {
      show(err instanceof Error ? err.message : 'Could not save your review', 'error');
    } finally { setBusy(false); }
  };

  const remove = async () => {
    setBusy(true);
    try { await deleteReview(slug); await load(); router.refresh(); show('Review deleted'); }
    catch { show('Could not delete your review', 'error'); }
    finally { setBusy(false); }
  };

  if (failed) return <p className="muted text-sm">Reviews could not be loaded right now.</p>;
  if (!data) return <div className="skeleton" style={{ height: 220 }} />;

  const { summary } = data;
  const max = Math.max(1, ...Object.values(summary.distribution));

  return (
    <div className="grid lg:grid-cols-[320px_1fr] gap-10">
      <div>
        <div className="flex items-end gap-3 mb-1">
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '3rem', lineHeight: 1 }}>{summary.average?.toFixed(1) ?? '–'}</span>
          <div className="pb-1"><Stars value={summary.average} size={18} /><p className="muted text-sm mt-1">{summary.count} review{summary.count !== 1 ? 's' : ''}</p></div>
        </div>
        <div className="flex flex-col gap-1.5 mt-5">
          {([5, 4, 3, 2, 1] as const).map(n => (
            <div key={n} className="flex items-center gap-2 text-xs muted">
              <span style={{ width: 10 }}>{n}</span><Star size={12} fill="#f59e0b" style={{ color: '#f59e0b' }} />
              <div className="flex-1 rounded-full overflow-hidden" style={{ height: 8, background: 'var(--btn-bg)' }}>
                <div style={{ width: `${(summary.distribution[String(n) as '1'] / max) * 100}%`, height: '100%', background: '#f59e0b' }} />
              </div>
              <span style={{ width: 22, textAlign: 'right' }}>{summary.distribution[String(n) as '1']}</span>
            </div>
          ))}
        </div>

        <div className="card p-5 mt-6">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', marginBottom: 12 }}>{mine ? 'Your review' : 'Write a review'}</h3>
          {!authLoading && !user ? (
            <p className="text-sm muted"><Link href="/auth/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>Sign in</Link> to share your experience.</p>
          ) : (
            <form onSubmit={submit} className="flex flex-col gap-3">
              <div className="flex gap-1" onMouseLeave={() => setHover(0)} role="radiogroup" aria-label="Your rating">
                {[1, 2, 3, 4, 5].map(n => (
                  <button key={n} type="button" role="radio" aria-checked={rating === n} aria-label={`${n} star${n > 1 ? 's' : ''}`}
                    onMouseEnter={() => setHover(n)} onClick={() => setRating(n)}>
                    <Star size={26} fill={(hover || rating) >= n ? '#f59e0b' : 'none'} style={{ color: (hover || rating) >= n ? '#f59e0b' : '#d9cdb8' }} />
                  </button>
                ))}
              </div>
              <input value={title} onChange={e => setTitle(e.target.value)} maxLength={120} placeholder="Headline (optional)" aria-label="Review headline" />
              <textarea value={body} onChange={e => setBody(e.target.value)} maxLength={2000} placeholder="What did you like or dislike?" aria-label="Review text" style={{ minHeight: 90, resize: 'vertical' }} />
              <div className="flex gap-2">
                <button className="btn-primary flex items-center gap-2" disabled={busy} style={{ padding: '10px 20px' }}>
                  {busy && <Loader2 size={15} className="animate-spin" />}{mine ? 'Update review' : 'Submit review'}
                </button>
                {mine && <button type="button" onClick={remove} disabled={busy} className="btn-ghost" style={{ padding: '10px 14px' }} aria-label="Delete my review"><Trash2 size={16} /></button>}
              </div>
            </form>
          )}
        </div>
      </div>

      <div>
        {data.results.length === 0 ? (
          <div className="card text-center py-14 px-6 muted">No reviews yet. Be the first to review this product.</div>
        ) : (
          <ul className="flex flex-col gap-5" style={{ listStyle: 'none' }}>
            {data.results.map(r => (
              <li key={r.id} className="card p-5">
                <div className="flex items-center justify-between gap-3 flex-wrap mb-2">
                  <Stars value={r.rating} size={16} />
                  <span className="text-xs muted">{timeAgo(r.created_at)}</span>
                </div>
                {r.title && <p style={{ fontWeight: 600, marginBottom: 4 }}>{r.title}</p>}
                {r.body && <p className="muted" style={{ lineHeight: 1.7, whiteSpace: 'pre-line' }}>{r.body}</p>}
                <p className="text-xs mt-3 flex items-center gap-2 flex-wrap muted">
                  <span style={{ fontWeight: 600, color: 'var(--fg)' }}>{r.is_mine ? `${r.author} (you)` : r.author}</span>
                  {r.verified_purchase && <span className="flex items-center gap-1" style={{ color: '#16a34a' }}><BadgeCheck size={14} /> Verified purchase</span>}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

import { ServerCrash } from 'lucide-react';

/** Shown when the API did not answer (free hosting sleeps after 15 minutes idle; the first request wakes it). */
export default function ApiDown({ what = 'the catalogue' }: { what?: string }) {
  return (
    <div className="card text-center mx-auto my-16 p-10" style={{ maxWidth: 520 }}>
      <ServerCrash size={44} style={{ color: 'var(--accent)', margin: '0 auto 16px' }} />
      <h2 className="section-title" style={{ fontSize: '1.4rem', marginBottom: 8 }}>The shop is waking up</h2>
      <p className="muted" style={{ lineHeight: 1.7, marginBottom: 20 }}>
        We couldn&apos;t load {what} just yet. The demo runs on free hosting that sleeps when idle, so the first visit can take up to a minute.
      </p>
      <a href="" className="btn-primary inline-block">Try again</a>
    </div>
  );
}

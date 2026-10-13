import Link from 'next/link';
import { Compass } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="text-center px-6 py-28">
      <Compass size={56} style={{ color: 'var(--accent)', margin: '0 auto 20px' }} />
      <h1 className="section-title" style={{ fontSize: '2.2rem', marginBottom: 10 }}>We couldn&apos;t find that page</h1>
      <p className="muted" style={{ marginBottom: 28 }}>The product or page you&apos;re after may have moved or never existed.</p>
      <div className="flex gap-3 justify-center flex-wrap">
        <Link href="/products" className="btn-primary">Browse products</Link>
        <Link href="/" className="btn-ghost">Back home</Link>
      </div>
    </div>
  );
}

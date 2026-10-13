'use client';
import { AlertTriangle } from 'lucide-react';

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="text-center px-6 py-28">
      <AlertTriangle size={52} style={{ color: '#dc2626', margin: '0 auto 20px' }} />
      <h1 className="section-title" style={{ fontSize: '2rem', marginBottom: 10 }}>Something went wrong</h1>
      <p className="muted" style={{ marginBottom: 28 }}>Please try again in a moment.</p>
      <button onClick={reset} className="btn-primary">Try again</button>
    </div>
  );
}

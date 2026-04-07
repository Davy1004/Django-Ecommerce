import Link from 'next/link';
import { CheckCircle, ArrowRight } from 'lucide-react';

export default function OrderSuccessPage() {
  return (
    <div className="max-w-lg mx-auto px-6 py-24 text-center">
      <div className="flex justify-center mb-8">
        <CheckCircle size={72} style={{ color: '#22c55e' }} />
      </div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.4rem', marginBottom: '16px' }}>
        Order Placed!
      </h1>
      <p style={{ color: 'var(--fg-muted)', lineHeight: 1.7, marginBottom: '40px', fontSize: '1.05rem' }}>
        Thank you for your purchase. We&apos;ve received your order and will process it shortly.
        A confirmation will be sent to your email.
      </p>
      <Link href="/products" className="btn-primary inline-flex items-center gap-2">
        Continue Shopping <ArrowRight size={16} />
      </Link>
    </div>
  );
}

'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { registerUser } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { Loader2, Package } from 'lucide-react';

export default function RegisterPage() {
  const [form, setForm] = useState({ username: '', email: '', password1: '', password2: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setUser } = useAuth();
  const router = useRouter();

  const set = (f: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(p => ({ ...p, [f]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password1 !== form.password2) { setError('Passwords do not match'); return; }
    setLoading(true);
    try {
      const res = await registerUser(form);
      setUser(res.user);
      router.push('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <Package size={32} style={{ color: 'var(--accent)', margin: '0 auto 12px' }} />
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', marginBottom: '8px' }}>Create account</h1>
          <p style={{ color: 'var(--fg-muted)' }}>Join ShopCraft today</p>
        </div>

        <div className="rounded-2xl p-8" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
          {error && (
            <div className="p-3 rounded-xl mb-5 text-sm" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Username</label>
              <input value={form.username} onChange={set('username')} required placeholder="your_username" />
            </div>
            <div>
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Email</label>
              <input type="email" value={form.email} onChange={set('email')} required placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Password</label>
              <input type="password" value={form.password1} onChange={set('password1')} required placeholder="••••••••" />
            </div>
            <div>
              <label className="block text-sm mb-1.5" style={{ color: 'var(--fg-muted)' }}>Confirm Password</label>
              <input type="password" value={form.password2} onChange={set('password2')} required placeholder="••••••••" />
            </div>
            <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center gap-2 mt-2">
              {loading ? <><Loader2 size={16} className="animate-spin" /> Creating account...</> : 'Create Account'}
            </button>
          </form>

          <p className="text-center mt-6 text-sm" style={{ color: 'var(--fg-muted)' }}>
            Already have an account?{' '}
            <Link href="/auth/login" style={{ color: 'var(--accent)' }} className="hover:opacity-70 transition-opacity">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

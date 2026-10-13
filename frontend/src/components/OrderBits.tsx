import { OrderDetail } from '@/lib/api';
import { slugify } from '@/lib/format';

export const STATUS_CLASS: Record<OrderDetail['status'], string> = {
  PAID: 'badge-paid', PENDING: 'badge-pending', CANCELLED: 'badge-cancelled',
};
export const STATUS_LABEL: Record<OrderDetail['status'], string> = {
  PAID: 'Paid', PENDING: 'Awaiting payment', CANCELLED: 'Cancelled',
};

export const StatusBadge = ({ status }: { status: OrderDetail['status'] }) =>
  <span className={`badge ${STATUS_CLASS[status]}`}>{STATUS_LABEL[status]}</span>;

/** Order lines only carry the product name, which is what the slug (and so the illustration) is built from. */
export const Thumb = ({ name, size = 56 }: { name: string; size?: number }) => (
  // eslint-disable-next-line @next/next/no-img-element
  <img src={`/products/${slugify(name)}.svg`} alt="" width={size} height={size} className="rounded-xl object-cover shrink-0"
    style={{ width: size, height: size, background: 'var(--card-img-bg)' }} />
);

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

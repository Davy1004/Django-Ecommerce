# ShopCraft API — Django REST + Next.js

**Live storefront:** https://django-ecommerce-theta.vercel.app (free tier: the API sleeps when idle, so the first load can take about a minute)

E-commerce backend with a checkout that is safe by design: the server (not the browser) decides prices,
stock is reserved atomically, orders can be retried without duplicates, and payments are verified by signature.

**Stack:** Django 5/6, Django REST Framework, JWT (SimpleJWT), PostgreSQL (SQLite for local dev), pytest · Next.js frontend in `frontend/`

## Run it locally
```bash
pip install -r requirements-dev.txt
cp .env.example .env                 # defaults work as-is
python manage.py migrate
python manage.py seed_demo           # demo categories + products
python manage.py createsuperuser     # optional: /admin
python manage.py runserver           # API on :8000

cd frontend && npm install && npm run dev      # shop on :3000
```
Tests: `pytest` (62 tests; 3 concurrency tests need PostgreSQL and are skipped on SQLite — run with `DATABASE_URL=postgres://... pytest`).

## API
| Method | Path | Notes |
|---|---|---|
| POST | `/accounts/api/register/` · `/login/` | returns `access` + `refresh` JWT |
| GET | `/accounts/api/me/` | needs `Authorization: Bearer <access>` |
| GET | `/api/products/` | `?category=slug&search=text&ordering=price&limit=&offset=` |
| GET | `/api/products/<slug>/` · `/api/categories/` · `/api/categories/<slug>/` | |
| POST | `/orders/api/checkout/` | `{items:[{product_id,quantity}], name,email,address,city,phone}` + `Idempotency-Key` header |
| POST | `/orders/api/orders/<id>/pay/` | `{payment_id, signature}` → order becomes `PAID` |
| POST | `/orders/api/orders/<id>/cancel/` | unpaid only; returns the stock |
| GET | `/orders/api/orders/` · `/orders/api/orders/<id>/` | your own orders only |
| POST | `/events/webhook/` | payment-provider webhook; signed, stored, processed later (see below) |
| GET | `/events/status/` | admin only: queue counts, oldest waiting age, retrying, recent dead events |
| GET | `/api/products/<slug>/reviews/` | rating summary + reviews (`verified_purchase` = has a PAID order for it) |
| POST · DELETE | `/api/products/<slug>/reviews/` | add/update or remove **your** review `{rating 1-5, title?, body?}` (one per user per product) |
| GET · POST | `/api/wishlist/` | your saved products · save one `{product_id}` (idempotent) |
| DELETE | `/api/wishlist/<product_id>/` | |
| POST | `/orders/api/coupons/validate/` | `{code, items}` → discount preview; nothing is redeemed until checkout (`coupon_code` on checkout) |
| GET | `/api/admin/sales/?days=30` | staff only: revenue, orders, top products, categories, coupons, low stock |
| GET | `/health/` | for the hosting platform |

## Features beyond checkout
- **Reviews and ratings:** one review per user per product, enforced by a unique constraint. Averages and counts come from the same query as the product list (no N+1), and `?ordering=rating` sorts best-rated first with unrated products last.
- **Wishlist:** per-user, idempotent add and remove, optimistic hearts in the UI.
- **Coupons:** percent or fixed, minimum order, cap, expiry, total and per-user limits. The discount is computed on the server inside the checkout transaction; the coupon row is locked so two buyers cannot take the last redemption, and cancelling or expiring an order gives the redemption back.
- **Order emails:** confirmation when an order is paid (by the user or by the webhook worker) and a notice when it is cancelled. Sent after the transaction commits; a mail-server failure is logged and never breaks the payment. Without SMTP settings the emails are printed to the server log.
- **Sales dashboard (`/dashboard`, staff only):** revenue per day, KPIs, top products, category split, coupon usage, low stock. Revenue counts PAID orders only.

## Payments
`PAYMENT_PROVIDER=mock` (default) needs no account. For Razorpay **test mode**: create free test keys, set
`PAYMENT_PROVIDER=razorpay`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`. The backend already creates the Razorpay order and
verifies the HMAC signature; the frontend currently completes a *mock* payment — wiring Razorpay's `checkout.js` popup is the one remaining step.

## Payment event pipeline (webhook → queue → worker)
Payment no longer depends on the customer's browser staying open. The provider POSTs a signed webhook; we verify, store, answer fast; a worker settles the order.
```
provider ─POST /events/webhook/─▶ verify HMAC ─▶ INSERT PaymentEvent(NEW) ─▶ 200
                                                        │ (the table is the queue)
              python manage.py process_events ◀─────────┘  SELECT … FOR UPDATE SKIP LOCKED
                 ├─ ok            → order PAID, event DONE
                 ├─ error         → retry with backoff (5s, 10s, 20s…), event stays NEW
                 └─ N failures / cancelled order → event DEAD  (replay from /admin once fixed)
```
Why it is safe: `UNIQUE(provider, event_id)` makes duplicate deliveries a no-op · claim + handle + result is one transaction, so a crashed worker just leaves the event waiting · `SKIP LOCKED` lets many workers run without double-handling · handlers are idempotent (at-least-once delivery).
Run: set `WEBHOOK_SECRET`, then `python manage.py process_events` (loops forever) or `--once` (drain and exit, for a scheduler).
Demo without a provider: `python manage.py send_test_webhook <order_id> --times 2` sends a signed `payment.captured` twice.
Tuning: `EVENT_MAX_ATTEMPTS`, `EVENT_BACKOFF_SECONDS`. Free hosting has no background workers: run `--once` from a free cron (cron-job.org / GitHub Actions) or run the loop locally for demos.
A `payment.captured` for an already-cancelled (expired) order goes straight to DEAD with "refund needed" — money was taken, so a human must refund it.

## Abandoned checkouts
Unpaid orders hold stock. `python manage.py expire_pending_orders` cancels those older than 30 min and returns the stock — run it on a schedule (Render cron / cron-job.org).

## Deploy for free (about 20 minutes, no card needed)
1. **Database - [Neon](https://neon.com):** create a project, copy the connection string. Do not use Render's free Postgres: it expires after 30 days.
2. **API - [Render](https://render.com):** *New → Blueprint*, pick this repo (it reads `render.yaml`). Paste the Neon string as `DATABASE_URL`. The build installs, migrates and seeds the demo shop (Render's free tier has no shell). Free services sleep after 15 min idle and take about a minute to wake.
3. **Frontend - [Vercel](https://vercel.com):** import the repo, set *Root Directory* to `frontend`, add `NEXT_PUBLIC_API_URL=https://<your-api>.onrender.com`.
4. Back in Render, set `CORS_ALLOWED_ORIGINS` to your Vercel address (no trailing slash) and let it redeploy.
5. **Worker (free):** Render's free tier has no background workers, so `.github/workflows/worker.yml` runs `process_events --once` and `expire_pending_orders` every hour from GitHub Actions. Add your Neon string as a repo secret named `DATABASE_URL` (Settings → Secrets and variables → Actions). You can also run it by hand from the Actions tab. Scheduled runs are free for public repos.

6. **Dashboard admin and emails (optional):** in Render set `ADMIN_USERNAME`, `ADMIN_EMAIL` and `ADMIN_PASSWORD`; every deploy runs `ensure_admin`, which creates or updates that staff user (it does nothing when they are empty, so no password is ever in the repo). Set `FRONTEND_URL` to your Vercel address so email links work. For real email delivery set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` plus `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` (any free SMTP, e.g. Gmail with an app password or Brevo); otherwise emails appear in the Render log.

Notes: uploaded product images need external storage in production (Render's disk is ephemeral), which is why the demo catalogue uses illustrations that ship with the frontend.

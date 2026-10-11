# ShopCraft API — Django REST + Next.js

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
| GET | `/health/` | for the hosting platform |

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

## Deploy for free
Render web service (`render.yaml`, `build.sh`) + free Postgres (Neon/Supabase) via `DATABASE_URL`; frontend on Vercel with `NEXT_PUBLIC_API_URL`.
Note: uploaded product images need external storage in production (Render's disk is ephemeral).

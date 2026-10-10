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
Tests: `pytest` (33 tests, ~15 s).

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
| GET | `/health/` | for the hosting platform |

## Payments
`PAYMENT_PROVIDER=mock` (default) needs no account. For Razorpay **test mode**: create free test keys, set
`PAYMENT_PROVIDER=razorpay`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`. The backend already creates the Razorpay order and
verifies the HMAC signature; the frontend currently completes a *mock* payment — wiring Razorpay's `checkout.js` popup is the one remaining step.

## Abandoned checkouts
Unpaid orders hold stock. `python manage.py expire_pending_orders` cancels those older than 30 min and returns the stock — run it on a schedule (Render cron / cron-job.org).

## Deploy for free
Render web service (`render.yaml`, `build.sh`) + free Postgres (Neon/Supabase) via `DATABASE_URL`; frontend on Vercel with `NEXT_PUBLIC_API_URL`.
Note: uploaded product images need external storage in production (Render's disk is ephemeral).

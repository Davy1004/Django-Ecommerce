# ShopCraft — Next.js Frontend

A full Next.js 14 frontend for your Django e-commerce backend.

## Quick Start

### 1. Start Django backend
```bash
cd ecommerce/
pip install django-cors-headers
python manage.py runserver
```

### 2. Start Next.js frontend
```bash
cd frontend/
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Pages & Routes

| Route | Description |
|-------|-------------|
| `/` | Home — featured products + categories (SSR) |
| `/products` | All products with category filter (SSR) |
| `/products/[slug]` | Product detail with add-to-cart |
| `/categories` | All categories |
| `/categories/[slug]` | Category with products (SSR) |
| `/cart` | Cart (client-side, localStorage) |
| `/checkout` | Checkout form → POST to Django API |
| `/order-success` | Confirmation page |
| `/auth/login` | Login → Django session auth |
| `/auth/register` | Register new user |

## Django API Endpoints Added

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List products (supports `?category=` & `?search=`) |
| GET | `/api/products/<slug>/` | Product detail |
| GET | `/api/categories/` | List all categories |
| GET | `/api/categories/<slug>/` | Category with products |
| POST | `/orders/api/checkout/` | Place an order |
| POST | `/accounts/api/login/` | Login |
| POST | `/accounts/api/register/` | Register |
| POST | `/accounts/api/logout/` | Logout |
| GET | `/accounts/api/me/` | Current user info |

## Environment Variables
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

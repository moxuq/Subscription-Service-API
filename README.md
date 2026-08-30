
# Subscription Service API

A service for creating and managing tariff-based subscriptions, featuring comprehensive statistics, authentication and a payment processing infrastructure.

Core stack: FastAPI, JWT, Redis, Celery, Alembic, PostgreSQL, Docker, Resend

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Register new user |
| POST | `/auth/login` | — | Login, get access + refresh tokens |
| POST | `/auth/refresh` | — | Refresh access token |
| GET | `/plans` | — | Get all plans (cached 1h) |
| GET | `/plans/{id}` | — | Get plan by ID |
| POST | `/subscriptions` | JWT | Create subscription (rate limit: 5 req/min) |
| GET | `/subscriptions/active` | JWT | Get active subscription (cached 5min) |
| DELETE | `/subscriptions` | JWT | Delete active subscription |
| DELETE | `/subscriptions/{id}` | JWT | Delete specific subscription |
| POST | `/subscriptions/{id}/cancel` | JWT | Cancel subscription |
| POST | `/payments/webhook` | HMAC | Payment status webhook (idempotent) |
| GET | `/admin/subscriptions` | Admin | Get all subscriptions (selectinload) |
| GET | `/admin/stats` | Admin | Get MRR, active subs, total users |

# Quick Start

```bash
git clone https://github.com/moxuq/Subscription-Service-API
cd subscription-service-api
docker-compose up --build
```

# Environment Variables

|  Variable      | Description                | Example |
| :--------      | :------------------------- |:--------|
| `DATABASE_URL` |Connection string           |`postgresql+asyncpg://postgres:postgres@db:5432/subscriptions`|
| `SECRET_KEY`   |32-byte secret cryptographic key    | - |
|`ALGORITHM`|Cryptographic signature|`HS256`|
|`ACCESS_TOKEN_MINUTES`|Access token validity period in minutes|`5-60`|
|`REFRESH_TOKEN_DAYS`|Refresh token validity period in days|`7-30`|
|`REDIS_URL`|Redis connection string|`redis://cache:6379/0`|
|`RESEND_API_KEY`|Your Resend API key|`re_xxxxx`|
|`RESEND_EMAIL`|Your Resend Email|`noreply@example.com`|
|`DEBUG`|Debug mode|`true`|

## Architecture

The service consists of 5 Docker containers:

| Service | Role |
|---------|------|
| **app** | FastAPI server (port 8000) |
| **db** | PostgreSQL 15 database |
| **cache** | Redis for caching and rate limiting |
| **worker** | Celery worker for background tasks |
| **beat** | Celery Beat scheduler |

**Background tasks:**
- `send_welcome_email` — triggered on user registration
- `send_payment_confirmation` — triggered after successful webhook
- `check_expired_subscriptions` — daily at 00:00, downgrades expired subs
- `send_expiry_warning` — daily at 09:00, warns users 3 days before expiry

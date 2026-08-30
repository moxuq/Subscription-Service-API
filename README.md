
# Subscription Service API

A service for creating and managing tariff-based subscriptions, featuring comprehensive statistics, authentication and a payment processing infrastructure.

Core stack: FastAPI, JWT, Redis, Celery, Alembic, PostgreSQL, Docker, Resend

```http
/auth/login - Log in to account
/auth/register - Register
/auth/refresh - Refresh token
/plans - Get all plans
/plans/{id} - Get plan by ID
/subscriptions - Get all subscriptions
/subscriptions/active - Get active subscription
/subscriptions/{id} - Get specific subscription
/payments/webhook - Payment status webhook
/admin/subscriptions - Get all subscriptions
/admin/stats - Get service statistics
```

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
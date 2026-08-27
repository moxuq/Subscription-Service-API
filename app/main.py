from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import hmac
import hashlib
import os

from .schemas import UserOut, UserCreate, Token, PlanOut, TokenRefresh, SubscriptionCreate, SubscriptionOut, WebhookPayload
from .crud import (create_user, 
                   get_user_by_email, 
                   get_all_plans, 
                   get_plan_id, 
                   create_subscription, 
                   get_active_subscription, 
                   del_active_subscription, 
                   del_subscription, 
                   cancel_subscription, 
                   mark_webhook_processed, 
                   is_webhook_processed, 
                   payment_status_to_paid,
                   subscription_status_to_active,
                   get_payment_by_order_id,
                   get_user_by_id)
from .database import get_db
from .auth import create_access_token, verify_password, create_refresh_token, get_current_user, check_refresh_token
from .models import User, ProcessedWebhook
from .tasks import send_welcome_email, send_payment_confirmation
from .redis_client import get_redis

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

@asynccontextmanager
async def lifespan():
    yield
    await get_redis().aclose()

app = FastAPI(title='Subscription Service API', lifespan=lifespan)

@app.post('/auth/register', response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await create_user(db, user)
    send_welcome_email.delay(new_user.email)
    return UserOut.model_validate(new_user)

@app.post('/auth/login', response_model=Token)
async def login(user: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.username)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Пользователь не найден')
    check_user = verify_password(user.password, db_user.hashed_password)
    if check_user == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный пароль')
    new_token = create_access_token(user.username)
    refresh_token = create_refresh_token(user.username)
    return {"access_token": new_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post('/auth/refresh', response_model=Token)
async def refresh(token: TokenRefresh, db: AsyncSession = Depends(get_db)):
    new_token = await check_refresh_token(token.refresh_token, db)
    return new_token

@app.get('/plans', response_model=list[PlanOut])
async def get_plans(db: AsyncSession = Depends(get_db)):
    plans = await get_all_plans(db)
    return plans

@app.get('/plans/{id}', response_model=PlanOut)
async def get_plan_by_id(id: int, db: AsyncSession = Depends(get_db)):
    plan = await get_plan_id(db, id)
    return plan


@app.post('/subscriptions', response_model=SubscriptionOut)
async def post_subscription(subscription: SubscriptionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_subscription = await create_subscription(db, user.id, subscription.plan_id)
    return new_subscription

@app.get('/subscriptions/active', response_model=SubscriptionOut)
async def get_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    subscription = await get_active_subscription(db, user.id)
    return subscription

@app.delete('/subscriptions', status_code=status.HTTP_204_NO_CONTENT)
async def delete_active_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await del_active_subscription(db, user.id)
    
@app.delete('/subscription/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await del_subscription(db, user.id, id)
    
@app.post('/subscriptions/{id}/cancel', response_model=SubscriptionOut)
async def post_cancel_subscription(id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    subscription = await cancel_subscription(db, user.id, id)
    return subscription

@app.post('/payments/webhook')
async def post_webhook(webhook: WebhookPayload, db: AsyncSession = Depends(get_db)):
    if not hmac.new(SECRET_KEY.encode(), f"{webhook.order_id}{webhook.status}{webhook.payment}".encode(), hashlib.sha256).hexdigest() == webhook.sign:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid signature')
    expected_sign = hmac.new(SECRET_KEY.encode(), f"{webhook.order_id}{webhook.status}{webhook.payment}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sign, webhook.sign):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверная сигнатура')
    processed_is = await is_webhook_processed(db, webhook.order_id)
    if processed_is == True:
        return {"status": "ok"}
    try:
        await mark_webhook_processed(db, webhook.order_id)
        await payment_status_to_paid(db, webhook.order_id)
        payment = await get_payment_by_order_id(db, webhook.order_id)
        if payment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Платеж не найден')
        subscription = await subscription_status_to_active(db, payment)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Подписка не найдена')
        user = await get_user_by_id(db, subscription.user_id)
        send_payment_confirmation.delay(user.email, float(payment.amount))
    except IntegrityError:
        pass
    return {"status": "ok"}
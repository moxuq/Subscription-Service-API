from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from .auth import hash_password
from .models import User, Plan, Subscription, Payment, ProcessedWebhook
from .schemas import UserCreate, StatsOut

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    db_user = await get_user_by_email(db, user.email)
    if db_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Пользователь с таким email уже существует')
    new_user = User(email=user.email, hashed_password=hash_password(user.password))
    await db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_all_plans(db: AsyncSession) -> list[Plan]:
    result = await db.execute(select(Plan).options(selectinload(Plan.subscriptions)))
    return result.scalars().all()

async def get_plan_by_id(db: AsyncSession, id: int) -> Plan | None:
    result = await db.execute(select(Plan).where(Plan.id == id))
    return result.scalar_one_or_none()

async def create_subscription(db: AsyncSession, user_id: int, plan_id: int) -> Subscription:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    plan = (await db.execute(select(Plan).where(Plan.id == plan_id))).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='План подписки не найден')
    exp = datetime.utcnow() + timedelta(days=plan.duration_days)
    existing = await get_active_subscription(db, user_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='У пользователя уже есть активная подписка')
    subscription = Subscription(user_id=user.id, plan_id=plan.id, started_at=datetime.utcnow(), expires_at=exp)
    await db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription

async def get_active_subscription(db: AsyncSession, user_id: int) -> Subscription | None:
    subscription = (await db.execute(select(Subscription).where(Subscription.user_id==user_id, Subscription.expires_at > datetime.utcnow()))).scalar_one_or_none()
    return subscription

async def create_payment(db: AsyncSession, subscription_id: int, order_id: str, amount: float) -> Payment:
    subscription = (await db.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Подписка не найдена')
    payment = Payment(subscription_id=subscription_id, order_id=order_id, amount=amount)
    await db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment

async def get_payment_by_order_id(db: AsyncSession, order_id: str) -> Payment | None:
    return (await db.execute(select(Payment).where(Payment.order_id == order_id))).scalar_one_or_none()

async def is_webhook_processed(db: AsyncSession, order_id: str) -> bool:
    webhook = (await db.execute(select(ProcessedWebhook).where(ProcessedWebhook.order_id == order_id))).scalar_one_or_none()
    return webhook is not None

async def mark_webhook_processed(db: AsyncSession, order_id: str):
    webhook = ProcessedWebhook(order_id=order_id)
    await db.add(webhook)
    await db.commit()
    
async def get_stats(db: AsyncSession) -> StatsOut:
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_subs = (await db.execute(select(func.count(Subscription.id)).where(Subscription.expires_at > datetime.utcnow()))).scalar() or 0
    stmt = select(func.coalesce(func.sum((Plan.price / Plan.duration_days) * 30), 0.0)).join(Plan, Subscription.plan_id == Plan.id).where(Subscription.expires_at > datetime.utcnow())
    mrr = float((await db.execute(stmt)).scalar())
    return StatsOut(mrr=mrr, total_users=total_users, active_subscriptions=active_subs)
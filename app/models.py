from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timezone
from typing import Literal
from enum import Enum

from .database import Base

class SubscriptionStatus(str, Enum):
    PENDING = 'pending'
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'
    PAST_DUE = 'past_due'

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    subscriptions: Mapped[list['Subscription']] = relationship(back_populates='user')
    
class Plan(Base):
    __tablename__ = 'plans'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    features: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    subscriptions: Mapped[list['Subscription']] = relationship(back_populates='plan')

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey('plans.id'), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(nullable=False, default='pending')
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    user: Mapped['User'] = relationship(back_populates='subscriptions')
    plan: Mapped['Plan'] = relationship(back_populates='subscriptions')
    payment: Mapped[list['Payment']] = relationship(back_populates='subscription')
    
    @hybrid_property
    def is_active(self):
        return self.status not in (SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED) and (self.expires_at is None or self.expires_at > datetime.now(timezone.utc))

class Payment(Base):
    __tablename__ = 'payments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey('subscriptions.id'), nullable=False)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    status: Mapped[Literal['pending', 'paid', 'failed']] = mapped_column(String(20), nullable=False, default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    subscription: Mapped['Subscription'] = relationship(back_populates='payment')
    
class ProcessedWebhook(Base):
    __tablename__ = 'processedwebhooks'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
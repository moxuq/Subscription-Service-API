from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Annotated, Literal, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field()]
    password: Annotated[str, Field(min_length=6, max_length=72)]
    
    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value
    
    model_config = ConfigDict(extra='forbid')

class UserLogin(BaseModel):
    email: Annotated[EmailStr, Field()]
    password: Annotated[str, Field(min_length=6, max_length=72)]

class UserOut(BaseModel):
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: Annotated[str, Field()]
    refresh_token: str
    token_type: Annotated[Literal['bearer'], Field()]
    
    model_config = ConfigDict(from_attributes=True)
    
class TokenRefresh(BaseModel):
    refresh_token: str

    model_config = ConfigDict(extra='forbid')

class PlanOut(BaseModel):
    id: int
    name: str
    price: float
    features: list[dict[str, Any]]
    duration_days: int
    
    model_config = ConfigDict(from_attributes=True)
    
class SubscriptionCreate(BaseModel):
    plan_id: Annotated[int, Field()]
    
    model_config = ConfigDict(extra='forbid')
    
class SubscriptionOut(BaseModel):
    id: int
    plan: PlanOut
    status: str
    started_at: datetime
    expires_at: datetime | None
    
    model_config = ConfigDict(from_attributes=True)
    
class SubscriptionAdminOut(BaseModel):
    id: int
    user: UserOut
    plan: PlanOut
    status: str
    started_at: datetime
    expires_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class WebhookPayload(BaseModel):
    order_id: str
    status: str
    payment: str
    sign: str
    
    model_config = ConfigDict(extra='forbid')
    
class StatsOut(BaseModel):
    mrr: float
    active_subscriptions: int
    total_users: int
    
    model_config = ConfigDict(from_attributes=True)
    
from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserOut, UserCreate, Token, PlanOut, TokenRefresh
from .crud import create_user, get_user_by_email, get_all_plans, get_plan_by_id
from .database import get_db
from .auth import create_access_token, verify_password, create_refresh_token

app = FastAPI(title='Subscription Service API')

@app.post('/auth/register', response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await create_user(db, user)
    return UserOut(new_user)

@app.post('/auth/login', response_model=Token)
async def login(user: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.username)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Пользователь не найден')
    check_user = verify_password(user.password, db_user.hashed_password)
    if check_user == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный пароль')
    new_token = create_access_token(user.username)
    return new_token

@app.post('/auth/refresh', response_model=Token)
async def refresh(token: TokenRefresh, user: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.username)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Пользователь не найден')
    check_user = verify_password(user.password, db_user.hashed_password)
    if check_user == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный пароль')
    new_token = create_refresh_token(user.username)
    return new_token

@app.get('/plans', response_model=list[PlanOut])
async def get_plans(db: AsyncSession = Depends(get_db)):
    plans = await get_all_plans(db)
    return plans

@app.get('/plans/{id}', response_model=PlanOut)
async def get_plan_by_id(id: int, db: AsyncSession = Depends(get_db)):
    plan = await get_plan_by_id(id, db)
    return plan

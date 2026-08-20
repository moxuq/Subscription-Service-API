from fastapi import FastAPI, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserOut, UserCreate, Token, UserLogin, TokenRefresh
from .crud import create_user, get_user_by_email
from .database import get_db
from .auth import create_access_token, verify_password

app = FastAPI(title='Subscription Service API')

@app.post('/auth/register', response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await create_user(db, user)
    return UserOut(new_user)

@app.post('/auth/login', response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Пользователь не найден')
    check_user = verify_password(user.password, db_user.hashed_password)
    if check_user == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный пароль')
    new_token = create_access_token(user.email)
    return new_token
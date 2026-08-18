from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import get_db
from .models import User
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=['argon2'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
ALGORITHM = os.getenv('ALGORITHM')
SECRET_KEY = os.getenv('SECRET_KEY')
REFRESH_TOKEN_DAYS = os.getenv('REFRESH_TOKEN_DAYS')
ACCESS_TOKEN_MINUTES = os.getenv('ACCESS_TOKEN_MINUTES')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user: OAuth2PasswordRequestForm) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    payload = {'sub': user.username, 'type': 'access', 'exp': exp}
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

def create_refresh_token(user: OAuth2PasswordRequestForm) -> str:
    exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)
    payload = {'sub': user.username, 'type': 'refresh', 'exp': exp}
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = jwt.decode(token, SECRET_KEY, [ALGORITHM])
    email = payload.get('sub')
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный токен')
    data = db.get(User, int(user.id))
    if data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Пользователь не найден')
    return data

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Доступ запрещен')
    return user
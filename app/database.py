from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'), echo=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        session.aclose()
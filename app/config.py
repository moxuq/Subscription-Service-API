from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Resend (email)
    RESEND_API_KEY: str
    RESEND_EMAIL: str
    
    # App
    APP_NAME: str = "Subscription Service API"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
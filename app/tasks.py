from celery.schedules import crontab
import resend
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .celery_app import celery_app
from .crud import active_to_expired_subscriptions, get_expiry_subscriptions

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
RESEND_EMAIL = os.getenv("RESEND_EMAIL")

DATABASE_URL = os.getenv('DATABASE_URL').replace('+asyncpg', '')
sync_engine = create_engine(DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False)

celery_app.conf.beat_schedule = {
    'check_expired': {
        'task': 'app.tasks.check_expired_subscriptions',
        'schedule': crontab(hour=0, minute=0),
    },
    'send_expiry_warning': {
        'task': 'app.tasks.send_expiry_warning',
        'schedule': crontab(hour=9, minute=0),
    },
}

celery_app.conf.timezone = 'Europe/Moscow'

@celery_app.task
def send_welcome_email(email: str):
    params = {
        "from": f"Acme <{RESEND_EMAIL}>",
        "to": [email],
        "subject": f"Welcome, {email}!"
    }
    resend.Emails.send(params)

@celery_app.task
def check_expired_subscriptions():
    with SyncSessionLocal() as db:
        active_to_expired_subscriptions(db)

@celery_app.task
def send_expiry_warning():
    with SyncSessionLocal() as db:
        subscriptions = get_expiry_subscriptions(db)
        emails = [sub.user.email for sub in subscriptions]
        params = {
            "from": f"Acme <{RESEND_EMAIL}>",
            "to": [emails],
            "subject": "Ваша подписка скоро закончится!"
        }
        resend.Emails.send(params)
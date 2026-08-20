from celery.schedules import crontab
import resend
from dotenv import load_dotenv
import os

from .celery_app import celery_app
from .crud import active_to_expired_subscriptions, get_expiry_subscriptions

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
RESEND_EMAIL = os.getenv("RESEND_EMAIL")

celery_app.conf.beat_schedule = {
    'check_expired': {
        'task': 'celery_app.check_expired_subscriptions',
        'schedule': crontab(hour=0, minute=0),
    },
    'send_expiry_warning': {
        'task': 'celery_app.send_expiry_warning',
        'schedule': crontab(hour=9, minute=0),
    },
}

celery_app.conf.timezone = 'Europe/Moscow'

@celery_app.task
def send_welcome_email(email: str):
    params: resend.Emails.SendParams = {
        "from": f"Acme {RESEND_EMAIL}",
        "to": [email],
        "subject": f"Welcome, {email}"
    }
    email = resend.Emails.send(params)
    
@celery_app.task
def check_expired_subscriptions():
    active_to_expired_subscriptions()

@celery_app.task
def send_expiry_warning(email: str):
    subscriptions = get_expiry_subscriptions()
    emails = subscriptions.user.email()
    params: resend.Emails.SendParams = {
        "from": f"Acme {RESEND_EMAIL}",
        "to": []
    }
from celery import Celery
from dotenv import load_dotenv
import os

REDIS_URL = os.getenv('REDIS_URL')


celery_app = Celery(
    'subscription_service',
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

celery_app.autodiscover_tasks(['app'])
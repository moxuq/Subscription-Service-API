import redis.asyncio as aioredis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL')

redis = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)

async def get_redis():
    yield redis
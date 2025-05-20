import redis.asyncio as redis
from kombu.utils.url import safequote
from config import redis as redis_config


def get_redis_client():
    host = safequote(redis_config['host'])
    return redis.Redis(
        host=host,
        port=redis_config['port'],
        db=0
    )


redis_client = get_redis_client()


async def add_key_value(key, value, expire=None):
    try:
        await redis_client.set(key, value)
        if expire:
            await redis_client.expire(key, expire)
    except redis.RedisError as e:
        raise Exception(f"Redis set failed: {str(e)}")


async def get_value(key):
    try:
        return await redis_client.get(key)
    except redis.RedisError as e:
        raise Exception(f"Redis get failed: {str(e)}")


async def delete_key(key):
    try:
        await redis_client.delete(key)
    except redis.RedisError as e:
        raise Exception(f"Redis delete failed: {str(e)}")


def _get_redis_client():
    host = safequote(redis_config['host'])
    return redis.Redis(
        host=host,
        port=redis_config['port'],
        db=0
    )

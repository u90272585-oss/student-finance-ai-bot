# cache.py
import redis
import json
import os
from typing import Optional, Any

# Проверяем, запущены ли тесты в CI (GitHub Actions)
IN_CI = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if IN_CI:
    # В CI используем фейковый клиент (не требует запущенного Redis)
    class FakeRedis:
        def get(self, key):
            return None

        def setex(self, key, ttl, value):
            return None

        def delete(self, key):
            return None

    redis_client = FakeRedis()
else:
    redis_client = redis.from_url(REDIS_URL)


def get_cached(key: str) -> Optional[Any]:
    """Получить данные из кэша"""
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def set_cached(key: str, value: Any, ttl: int = 300) -> None:
    """Сохранить в кэш (ttl в секундах)"""
    redis_client.setex(key, ttl, json.dumps(value, default=str))


def delete_cached(key: str) -> None:
    """Удалить из кэша"""
    redis_client.delete(key)


def clear_user_cache(user_id: int) -> None:
    """Очистить все кэши пользователя"""
    delete_cached(f"user:{user_id}")
    delete_cached(f"transactions:{user_id}")
    delete_cached(f"goals:{user_id}")


def row_to_dict(row) -> dict:
    """Конвертирует sqlite3.Row или asyncpg.Row в dict"""
    if row is None:
        return None

    if hasattr(row, 'keys'):
        return dict(row)

    # Для tuple — возвращаем как есть, но с числовыми ключами
    if isinstance(row, tuple):
        return {i: val for i, val in enumerate(row)}

    return dict(row)
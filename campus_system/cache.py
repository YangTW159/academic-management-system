"""Redis 缓存层：可选启用，Redis 未运行时自动降级跳过。"""
import json
import logging

import redis
from flask import request, g

logger = logging.getLogger(__name__)

_redis_client = None


def init_redis(app):
    """在应用工厂中初始化 Redis 连接（可选）。"""
    global _redis_client
    url = app.config.get("REDIS_URL")
    if not url:
        logger.info("REDIS_URL 未配置，缓存层已禁用")
        return
    try:
        _redis_client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        _redis_client.ping()
        app.logger.info("Redis 连接成功: %s", url)
    except Exception as e:
        _redis_client = None
        app.logger.warning("Redis 不可用，缓存层降级: %s", e)


def cache_get(key):
    if not _redis_client:
        return None
    try:
        val = _redis_client.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key, value, ttl=60):
    if not _redis_client:
        return
    try:
        _redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        pass


def cache_delete_prefix(prefix):
    if not _redis_client:
        return
    try:
        for key in _redis_client.scan_iter(f"{prefix}*"):
            _redis_client.delete(key)
    except Exception:
        pass


def cached(prefix, ttl=60):
    """装饰器：对 GET 接口做缓存，按 URL + 查询参数生成 key。"""
    def decorator(view_func):
        def wrapper(*args, **kwargs):
            key = f"{prefix}:{request.path}:{request.query_string.decode()}"
            cached = cache_get(key)
            if cached is not None:
                return cached
            result = view_func(*args, **kwargs)
            cache_set(key, result, ttl)
            return result
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator

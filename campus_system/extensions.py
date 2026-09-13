from functools import wraps

from flask import jsonify, request, session
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from campus_system.config import ROLE_LABELS


class ServiceError(Exception):
    """业务异常：路由中 raise ServiceError('xxx') 即返回对应 HTTP 错误。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def current_user():
    """优先从 session 取（前端兼容），其次从 JWT 取。"""
    user = session.get("user")
    if user:
        return user
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            return identity
    except Exception:
        pass
    return None


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"message": "请先登录系统"}), 401
        return view_func(*args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"message": "请先登录系统"}), 401
            if user["role"] not in roles:
                return jsonify({"message": "无权执行该操作"}), 403
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def get_json_body():
    return request.get_json(silent=True) or {}


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def record_log(actor, action_name, target_name):
    """记录操作日志（ORM 版）。"""
    from campus_system.models import OperationLog
    log = OperationLog(actor=actor, action_name=action_name, target_name=target_name)
    from campus_system.db import db
    db.session.add(log)
    db.session.commit()


__all__ = [
    "ServiceError",
    "current_user",
    "login_required",
    "role_required",
    "get_json_body",
    "parse_bool",
    "record_log",
    "ROLE_LABELS",
]

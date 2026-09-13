from functools import wraps

from flask import jsonify, request, session

from campus_system.config import ROLE_LABELS


class ServiceError(Exception):
    """业务异常：路由中 raise ServiceError('xxx') 即返回对应 HTTP 错误。"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def current_user():
    return session.get("user")


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


def record_log(cursor, actor, action_name, target_name):
    cursor.execute(
        """
        INSERT INTO operation_log (actor, action_name, target_name)
        VALUES (%s, %s, %s)
        """,
        (actor, action_name, target_name),
    )


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

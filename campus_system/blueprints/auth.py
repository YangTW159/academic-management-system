from flask import Blueprint, jsonify, request, session

from campus_system.db import db_cursor, fetch_one
from campus_system.extensions import (
    ROLE_LABELS,
    ServiceError,
    current_user,
    get_json_body,
    record_log,
)

bp = Blueprint("auth", __name__)


@bp.post("/api/login")
def login():
    body = get_json_body()
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        raise ServiceError("用户名和密码不能为空")

    user_row = fetch_one(
        """
        SELECT user_id, username, role_name, display_name, related_id, status
        FROM sys_user
        WHERE username = %s AND password = %s
        """,
        (username, password),
    )
    if not user_row or user_row["status"] != "active":
        raise ServiceError("用户名或密码错误", 401)

    session["user"] = {
        "id": user_row["user_id"],
        "username": user_row["username"],
        "role": user_row["role_name"],
        "display_name": user_row["display_name"],
        "role_label": ROLE_LABELS.get(user_row["role_name"], user_row["role_name"]),
        "related_id": user_row["related_id"],
    }

    with db_cursor(commit=True) as (_, cursor):
        record_log(cursor, user_row["display_name"], "登录系统", user_row["username"])

    return jsonify({"message": "登录成功", "user": session["user"]})


@bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "已退出登录"})


@bp.get("/api/session")
def session_info():
    user = current_user()
    if not user:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user": user})

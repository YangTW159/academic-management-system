from flask import Blueprint, jsonify, request, session
from flask_jwt_extended import create_access_token

from campus_system.db import db
from campus_system.extensions import (
    ROLE_LABELS,
    ServiceError,
    current_user,
    get_json_body,
    record_log,
)
from campus_system.models import SysUser

bp = Blueprint("auth", __name__)


@bp.post("/api/login")
def login():
    """用户登录
    ---
    tags:
      - 认证
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: [username, password]
          properties:
            username: {type: string, example: admin}
            password: {type: string, example: "123456"}
    responses:
      200:
        description: 登录成功，返回用户信息和 JWT token
      401:
        description: 用户名或密码错误
    """
    body = get_json_body()
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        raise ServiceError("用户名和密码不能为空")

    user_row = SysUser.query.filter_by(username=username, password=password).first()
    if not user_row or user_row.status != "active":
        raise ServiceError("用户名或密码错误", 401)

    user_info = {
        "id": user_row.user_id,
        "username": user_row.username,
        "role": user_row.role_name,
        "display_name": user_row.display_name,
        "role_label": ROLE_LABELS.get(user_row.role_name, user_row.role_name),
        "related_id": user_row.related_id,
    }

    # 同时写 session（前端兼容）和 JWT token
    session["user"] = user_info
    access_token = create_access_token(identity=user_info)

    record_log(user_row.display_name, "登录系统", user_row.username)

    return jsonify({
        "message": "登录成功",
        "user": user_info,
        "access_token": access_token,
        "token_type": "Bearer",
    })


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

from flask import Blueprint, jsonify, request

from campus_system.db import db_cursor, fetch_one
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    parse_bool,
    record_log,
    role_required,
)
from campus_system.services import get_visible_notices

bp = Blueprint("notices", __name__)


@bp.get("/api/notices")
@login_required
def notice_list():
    user = current_user()
    keyword = request.args.get("keyword") or ""
    return jsonify(get_visible_notices(user, keyword))


@bp.post("/api/notices")
@role_required("admin", "teacher", "dormManager")
def add_notice():
    user = current_user()
    body = get_json_body()
    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    if not title or not content:
        raise ServiceError("标题和内容不能为空")

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            """
            INSERT INTO notice
              (title, content, publisher, publisher_role, scope, category, pinned, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                title, content,
                user["display_name"], user["role"],
                body.get("scope") or "全校",
                body.get("category") or "学校",
                1 if parse_bool(body.get("pinned")) else 0,
                body.get("status") or "已发布",
            ),
        )
        record_log(cursor, user["display_name"], "发布公告", title)
        notice_id = cursor.lastrowid

    row = fetch_one(
        """
        SELECT nid, title, content,
               DATE_FORMAT(publish_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS publish_time,
               publisher, publisher_role, scope, category, pinned, status
        FROM notice WHERE nid = %s
        """,
        (notice_id,),
    )
    return jsonify({"message": "公告已发布", "data": row}), 201


@bp.put("/api/notices/<int:nid>")
@role_required("admin", "teacher", "dormManager")
def edit_notice(nid):
    user = current_user()
    body = get_json_body()

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            "SELECT nid, publisher, title, content, scope, category, pinned, status FROM notice WHERE nid = %s",
            (nid,),
        )
        notice_row = cursor.fetchone()
        if not notice_row:
            raise ServiceError("公告不存在", 404)
        if user["role"] != "admin" and notice_row["publisher"] != user["display_name"]:
            raise ServiceError("只能修改自己发布的公告", 403)

        cursor.execute(
            """
            UPDATE notice SET
              title = %s, content = %s, scope = %s, category = %s, pinned = %s, status = %s
            WHERE nid = %s
            """,
            (
                body.get("title") or notice_row["title"],
                body.get("content") or notice_row["content"],
                body.get("scope") or notice_row["scope"],
                body.get("category") or notice_row["category"],
                1 if parse_bool(body.get("pinned")) else 0,
                body.get("status") or notice_row["status"],
                nid,
            ),
        )
        record_log(cursor, user["display_name"], "修改公告",
                   body.get("title") or notice_row["title"])

    row = fetch_one(
        """
        SELECT nid, title, content,
               DATE_FORMAT(publish_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS publish_time,
               publisher, publisher_role, scope, category, pinned, status
        FROM notice WHERE nid = %s
        """,
        (nid,),
    )
    return jsonify({"message": "公告已更新", "data": row})


@bp.delete("/api/notices/<int:nid>")
@role_required("admin", "teacher", "dormManager")
def delete_notice(nid):
    user = current_user()
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT nid, publisher, title FROM notice WHERE nid = %s", (nid,))
        notice_row = cursor.fetchone()
        if not notice_row:
            raise ServiceError("公告不存在", 404)
        if user["role"] != "admin" and notice_row["publisher"] != user["display_name"]:
            raise ServiceError("只能删除自己发布的公告", 403)
        cursor.execute("DELETE FROM notice WHERE nid = %s", (nid,))
        record_log(cursor, user["display_name"], "删除公告", notice_row["title"])
    return jsonify({"message": "公告已删除"})

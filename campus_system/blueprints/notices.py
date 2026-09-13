from flask import Blueprint, jsonify, request

from campus_system.db import db
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    parse_bool,
    record_log,
    role_required,
)
from campus_system.models import Notice
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

    notice = Notice(
        title=title, content=content,
        publisher=user["display_name"], publisher_role=user["role"],
        scope=body.get("scope") or "全校",
        category=body.get("category") or "学校",
        pinned=bool(parse_bool(body.get("pinned"))),
        status=body.get("status") or "已发布",
    )
    db.session.add(notice)
    db.session.commit()
    record_log(user["display_name"], "发布公告", title)

    return jsonify({"message": "公告已发布", "data": notice.to_dict()}), 201


@bp.put("/api/notices/<int:nid>")
@role_required("admin", "teacher", "dormManager")
def edit_notice(nid):
    user = current_user()
    body = get_json_body()

    notice = Notice.query.filter_by(nid=nid).first()
    if not notice:
        raise ServiceError("公告不存在", 404)
    if user["role"] != "admin" and notice.publisher != user["display_name"]:
        raise ServiceError("只能修改自己发布的公告", 403)

    if "title" in body:
        notice.title = body["title"]
    if "content" in body:
        notice.content = body["content"]
    if "scope" in body:
        notice.scope = body["scope"]
    if "category" in body:
        notice.category = body["category"]
    if "pinned" in body:
        notice.pinned = bool(parse_bool(body["pinned"]))
    if "status" in body:
        notice.status = body["status"]

    db.session.commit()
    record_log(user["display_name"], "修改公告", notice.title)
    return jsonify({"message": "公告已更新", "data": notice.to_dict()})


@bp.delete("/api/notices/<int:nid>")
@role_required("admin", "teacher", "dormManager")
def delete_notice(nid):
    user = current_user()
    notice = Notice.query.filter_by(nid=nid).first()
    if not notice:
        raise ServiceError("公告不存在", 404)
    if user["role"] != "admin" and notice.publisher != user["display_name"]:
        raise ServiceError("只能删除自己发布的公告", 403)
    title = notice.title
    db.session.delete(notice)
    db.session.commit()
    record_log(user["display_name"], "删除公告", title)
    return jsonify({"message": "公告已删除"})

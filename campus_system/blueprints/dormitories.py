from flask import Blueprint, jsonify

from campus_system.db import db
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    record_log,
    role_required,
)
from campus_system.models import DormManager, Dormitory

bp = Blueprint("dormitories", __name__)


def _dorm_to_dict(row):
    return {
        "dorm_id": row.dorm_id, "building": row.building, "room": row.room,
        "max_num": row.max_num, "cur_num": row.cur_num, "dm_id": row.dm_id,
        "status": row.status,
        "available_beds": row.max_num - row.cur_num,
        "manager_name": row.dm_name if hasattr(row, "dm_name") else None,
    }


@bp.get("/api/dormitories")
@login_required
def dormitory_list():
    user = current_user()
    query = db.session.query(
        Dormitory, DormManager.dm_name
    ).outerjoin(DormManager, Dormitory.dm_id == DormManager.dm_id)

    if user["role"] == "dormManager":
        query = query.filter(Dormitory.dm_id == user["related_id"])

    rows = query.order_by(Dormitory.building, Dormitory.room).all()
    result = []
    for dorm, dm_name in rows:
        d = dorm.to_dict()
        d["available_beds"] = dorm.max_num - dorm.cur_num
        d["manager_name"] = dm_name
        result.append(d)
    return jsonify(result)


@bp.post("/api/dormitories")
@role_required("admin", "dormManager")
def add_dormitory():
    user = current_user()
    body = get_json_body()
    dorm_id = (body.get("dorm_id") or "").strip()
    building = (body.get("building") or "").strip()
    room = (body.get("room") or "").strip()
    dm_id = (body.get("dm_id") or "").strip()
    max_num = int(body.get("max_num") or 4)
    cur_num = int(body.get("cur_num") or 0)

    if not dorm_id or not building or not room or not dm_id:
        raise ServiceError("宿舍号、楼栋、房间号、宿管不能为空")
    if cur_num > max_num:
        raise ServiceError("已住人数不能大于可住人数")
    if user["role"] == "dormManager" and dm_id != user["related_id"]:
        raise ServiceError("宿管只能维护自己负责的宿舍", 403)

    if Dormitory.query.filter_by(dorm_id=dorm_id).first():
        raise ServiceError("宿舍号已存在")
    if not DormManager.query.filter_by(dm_id=dm_id).first():
        raise ServiceError("宿管不存在")

    dorm = Dormitory(
        dorm_id=dorm_id, building=building, room=room,
        max_num=max_num, cur_num=cur_num, dm_id=dm_id,
        status=body.get("status") or "正常",
    )
    db.session.add(dorm)
    db.session.commit()
    record_log(user["display_name"], "新增宿舍", dorm_id)

    return jsonify({"message": "宿舍已新增", "data": dorm.to_dict()}), 201


@bp.put("/api/dormitories/<dorm_id>")
@role_required("admin", "dormManager")
def edit_dormitory(dorm_id):
    user = current_user()
    body = get_json_body()

    dorm = Dormitory.query.filter_by(dorm_id=dorm_id).first()
    if not dorm:
        raise ServiceError("宿舍不存在", 404)
    if user["role"] == "dormManager" and dorm.dm_id != user["related_id"]:
        raise ServiceError("宿管只能维护自己负责的宿舍", 403)

    next_dm_id = dorm.dm_id if user["role"] == "dormManager" else (body.get("dm_id") or dorm.dm_id)
    next_max_num = int(body.get("max_num") or dorm.max_num)
    next_cur_num = int(body.get("cur_num") or dorm.cur_num)
    if next_cur_num > next_max_num:
        raise ServiceError("已住人数不能大于可住人数")

    if not DormManager.query.filter_by(dm_id=next_dm_id).first():
        raise ServiceError("宿管不存在")

    if "building" in body:
        dorm.building = body["building"]
    if "room" in body:
        dorm.room = body["room"]
    dorm.max_num = next_max_num
    dorm.cur_num = next_cur_num
    dorm.dm_id = next_dm_id
    if "status" in body:
        dorm.status = body["status"]

    db.session.commit()
    record_log(user["display_name"], "更新宿舍", dorm_id)
    return jsonify({"message": "宿舍已更新", "data": dorm.to_dict()})

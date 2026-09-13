from flask import Blueprint, jsonify

from campus_system.db import db_cursor, fetch_all, fetch_one
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    record_log,
    role_required,
)

bp = Blueprint("dormitories", __name__)

_DORM_SELECT = """
    SELECT
      d.dorm_id, d.building, d.room, d.max_num, d.cur_num, d.dm_id, d.status,
      (d.max_num - d.cur_num) AS available_beds,
      dm.dm_name AS manager_name
    FROM dormitory d
    LEFT JOIN dorm_manager dm ON d.dm_id = dm.dm_id
"""


@bp.get("/api/dormitories")
@login_required
def dormitory_list():
    user = current_user()
    params = []
    where_sql = ""
    if user["role"] == "dormManager":
        where_sql = "WHERE d.dm_id = %s"
        params.append(user["related_id"])
    rows = fetch_all(
        f"{_DORM_SELECT} {where_sql} ORDER BY d.building, d.room", params
    )
    return jsonify(rows)


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

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT dorm_id FROM dormitory WHERE dorm_id = %s", (dorm_id,))
        if cursor.fetchone():
            raise ServiceError("宿舍号已存在")
        cursor.execute("SELECT dm_id FROM dorm_manager WHERE dm_id = %s", (dm_id,))
        if not cursor.fetchone():
            raise ServiceError("宿管不存在")
        cursor.execute(
            """
            INSERT INTO dormitory (dorm_id, building, room, max_num, cur_num, dm_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (dorm_id, building, room, max_num, cur_num, dm_id,
             body.get("status") or "正常"),
        )
        record_log(cursor, user["display_name"], "新增宿舍", dorm_id)

    row = fetch_one(f"{_DORM_SELECT} WHERE d.dorm_id = %s", (dorm_id,))
    return jsonify({"message": "宿舍已新增", "data": row}), 201


@bp.put("/api/dormitories/<dorm_id>")
@role_required("admin", "dormManager")
def edit_dormitory(dorm_id):
    user = current_user()
    body = get_json_body()

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            "SELECT dorm_id, dm_id, max_num, cur_num, building, room, status FROM dormitory WHERE dorm_id = %s",
            (dorm_id,),
        )
        dorm_row = cursor.fetchone()
        if not dorm_row:
            raise ServiceError("宿舍不存在", 404)
        if user["role"] == "dormManager" and dorm_row["dm_id"] != user["related_id"]:
            raise ServiceError("宿管只能维护自己负责的宿舍", 403)

        next_dm_id = dorm_row["dm_id"] if user["role"] == "dormManager" else (body.get("dm_id") or dorm_row["dm_id"])
        next_max_num = int(body.get("max_num") or dorm_row["max_num"])
        next_cur_num = int(body.get("cur_num") or dorm_row["cur_num"])
        if next_cur_num > next_max_num:
            raise ServiceError("已住人数不能大于可住人数")

        cursor.execute("SELECT dm_id FROM dorm_manager WHERE dm_id = %s", (next_dm_id,))
        if not cursor.fetchone():
            raise ServiceError("宿管不存在")

        cursor.execute(
            """
            UPDATE dormitory SET
              building = %s, room = %s, max_num = %s, cur_num = %s,
              dm_id = %s, status = %s
            WHERE dorm_id = %s
            """,
            (
                body.get("building") or dorm_row["building"],
                body.get("room") or dorm_row["room"],
                next_max_num, next_cur_num, next_dm_id,
                body.get("status") or dorm_row["status"],
                dorm_id,
            ),
        )
        record_log(cursor, user["display_name"], "更新宿舍", dorm_id)

    row = fetch_one(f"{_DORM_SELECT} WHERE d.dorm_id = %s", (dorm_id,))
    return jsonify({"message": "宿舍已更新", "data": row})

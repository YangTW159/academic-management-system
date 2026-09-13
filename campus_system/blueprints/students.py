from flask import Blueprint, jsonify, request

from campus_system.db import db_cursor, fetch_all, fetch_one
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    record_log,
    role_required,
)
from campus_system.services import get_student_profile

bp = Blueprint("students", __name__)


# ---------- 基础数据下拉 ----------
@bp.get("/api/classes")
@login_required
def classes():
    rows = fetch_all(
        "SELECT class_id, class_name, major, college FROM class_info ORDER BY class_id"
    )
    return jsonify(rows)


@bp.get("/api/teachers")
@login_required
def teachers():
    rows = fetch_all("SELECT tno, tname, tgender, tedu, tpro FROM teacher ORDER BY tno")
    return jsonify(rows)


@bp.get("/api/dorm-managers")
@login_required
def dorm_managers():
    rows = fetch_all(
        "SELECT dm_id, dm_name, dm_gender, dm_phone FROM dorm_manager ORDER BY dm_id"
    )
    return jsonify(rows)


# ---------- 学生 CRUD ----------
@bp.get("/api/students")
@login_required
def student_list():
    user = current_user()
    keyword = (request.args.get("keyword") or "").strip()
    where_clauses = []
    params = []

    if user["role"] == "student":
        where_clauses.append("s.sno = %s")
        params.append(user["related_id"])
    elif user["role"] == "dormManager":
        where_clauses.append("d.dm_id = %s")
        params.append(user["related_id"])
    elif user["role"] == "teacher":
        where_clauses.append(
            """
            EXISTS (
              SELECT 1 FROM sc sc1
              JOIN course c1 ON sc1.cno = c1.cno
              WHERE sc1.sno = s.sno AND c1.tno = %s
            )
            """
        )
        params.append(user["related_id"])

    if keyword:
        where_clauses.append("(s.sno LIKE %s OR s.sname LIKE %s OR c.class_name LIKE %s)")
        like_value = f"%{keyword}%"
        params.extend([like_value, like_value, like_value])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    rows = fetch_all(
        f"""
        SELECT
          s.sno, s.sname, s.sgender,
          DATE_FORMAT(s.sbirth, '%%Y-%%m-%%d') AS sbirth,
          s.sphone, s.class_id, s.dorm_id, s.status,
          c.class_name, c.major, c.college,
          CASE WHEN d.dorm_id IS NULL THEN '未分配'
               ELSE CONCAT(d.building, '-', d.room) END AS dorm_summary
        FROM student s
        LEFT JOIN class_info c ON s.class_id = c.class_id
        LEFT JOIN dormitory d ON s.dorm_id = d.dorm_id
        {where_sql}
        ORDER BY s.sno
        """,
        params,
    )
    return jsonify(rows)


@bp.post("/api/students")
@role_required("admin")
def add_student():
    user = current_user()
    body = get_json_body()
    sno = (body.get("sno") or "").strip()
    sname = (body.get("sname") or "").strip()
    class_id = (body.get("class_id") or "").strip()
    dorm_id = (body.get("dorm_id") or "").strip() or None
    status = (body.get("status") or "在读").strip()

    if not sno or not sname or not class_id:
        raise ServiceError("学号、姓名、班级不能为空")

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT sno FROM student WHERE sno = %s", (sno,))
        if cursor.fetchone():
            raise ServiceError("学号已存在")
        cursor.execute("SELECT class_id FROM class_info WHERE class_id = %s", (class_id,))
        if not cursor.fetchone():
            raise ServiceError("班级不存在")

        if dorm_id:
            cursor.execute(
                "SELECT dorm_id, max_num, cur_num FROM dormitory WHERE dorm_id = %s",
                (dorm_id,),
            )
            dorm_row = cursor.fetchone()
            if not dorm_row:
                raise ServiceError("宿舍不存在")
            if int(dorm_row["cur_num"]) >= int(dorm_row["max_num"]):
                raise ServiceError("宿舍床位已满，无法分配")

        cursor.execute(
            """
            INSERT INTO student (sno, sname, sgender, sbirth, sphone, class_id, dorm_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                sno, sname,
                body.get("sgender") or None,
                body.get("sbirth") or None,
                body.get("sphone") or None,
                class_id, dorm_id, status,
            ),
        )
        if dorm_id and status not in {"退学", "毕业"}:
            cursor.execute(
                "UPDATE dormitory SET cur_num = cur_num + 1 WHERE dorm_id = %s",
                (dorm_id,),
            )
        record_log(cursor, user["display_name"], "新增学生", sno)

    return jsonify({"message": "学生信息已新增", "data": get_student_profile(sno)}), 201


@bp.put("/api/students/<sno>")
@role_required("admin")
def edit_student(sno):
    user = current_user()
    body = get_json_body()

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            "SELECT sno, dorm_id, status FROM student WHERE sno = %s", (sno,)
        )
        student_row = cursor.fetchone()
        if not student_row:
            raise ServiceError("学生不存在", 404)

        next_dorm_id = (body.get("dorm_id") if "dorm_id" in body else student_row["dorm_id"]) or None
        next_status = (body.get("status") if "status" in body else student_row["status"]) or student_row["status"]
        old_dorm_id = student_row["dorm_id"]

        if "class_id" in body:
            cursor.execute("SELECT class_id FROM class_info WHERE class_id = %s", (body["class_id"],))
            if not cursor.fetchone():
                raise ServiceError("班级不存在")

        if next_dorm_id and next_dorm_id != old_dorm_id and next_status not in {"退学", "毕业"}:
            cursor.execute(
                "SELECT dorm_id, max_num, cur_num FROM dormitory WHERE dorm_id = %s",
                (next_dorm_id,),
            )
            new_dorm_row = cursor.fetchone()
            if not new_dorm_row:
                raise ServiceError("目标宿舍不存在")
            if int(new_dorm_row["cur_num"]) >= int(new_dorm_row["max_num"]):
                raise ServiceError("目标宿舍已满")

        profile = get_student_profile(sno)
        cursor.execute(
            """
            UPDATE student SET
              sname = %s, sgender = %s, sbirth = %s, sphone = %s,
              class_id = %s, dorm_id = %s, status = %s
            WHERE sno = %s
            """,
            (
                body.get("sname") or profile["sname"],
                body.get("sgender") if "sgender" in body else profile["sgender"],
                body.get("sbirth") if "sbirth" in body else profile["sbirth"],
                body.get("sphone") if "sphone" in body else profile["sphone"],
                body.get("class_id") or profile["class_id"],
                None if next_status in {"退学", "毕业"} else next_dorm_id,
                next_status,
                sno,
            ),
        )

        final_dorm_id = None if next_status in {"退学", "毕业"} else next_dorm_id
        if old_dorm_id and old_dorm_id != final_dorm_id:
            cursor.execute(
                "UPDATE dormitory SET cur_num = GREATEST(cur_num - 1, 0) WHERE dorm_id = %s",
                (old_dorm_id,),
            )
        if final_dorm_id and final_dorm_id != old_dorm_id and next_status not in {"退学", "毕业"}:
            cursor.execute(
                "UPDATE dormitory SET cur_num = cur_num + 1 WHERE dorm_id = %s",
                (final_dorm_id,),
            )
        record_log(cursor, user["display_name"], "更新学生", sno)

    return jsonify({"message": "学生信息已更新", "data": get_student_profile(sno)})


@bp.delete("/api/students/<sno>")
@role_required("admin")
def delete_student(sno):
    user = current_user()
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT dorm_id FROM student WHERE sno = %s", (sno,))
        student_row = cursor.fetchone()
        if not student_row:
            raise ServiceError("学生不存在", 404)
        if student_row["dorm_id"]:
            cursor.execute(
                "UPDATE dormitory SET cur_num = GREATEST(cur_num - 1, 0) WHERE dorm_id = %s",
                (student_row["dorm_id"],),
            )
        cursor.execute("DELETE FROM sc WHERE sno = %s", (sno,))
        cursor.execute("DELETE FROM student WHERE sno = %s", (sno,))
        record_log(cursor, user["display_name"], "删除学生", sno)
    return jsonify({"message": "学生信息已删除"})

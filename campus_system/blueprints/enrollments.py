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

bp = Blueprint("enrollments", __name__)

_SCORE_SELECT = """
    SELECT sc.sno, sc.cno, sc.score,
           s.sname AS student_name, c.cname AS course_name,
           CASE WHEN sc.score IS NULL THEN NULL
                ELSE ROUND(GREATEST(sc.score - 50, 0) / 10, 1) END AS gpa_point
    FROM sc
    JOIN student s ON sc.sno = s.sno
    JOIN course c ON sc.cno = c.cno
"""


@bp.get("/api/enrollments")
@login_required
def enrollment_list():
    user = current_user()
    where_sql = ""
    params = []
    if user["role"] == "student":
        where_sql = "WHERE sc.sno = %s"
        params.append(user["related_id"])
    elif user["role"] == "teacher":
        where_sql = "WHERE c.tno = %s"
        params.append(user["related_id"])
    elif user["role"] == "dormManager":
        where_sql = "WHERE 1 = 0"

    rows = fetch_all(
        f"{_SCORE_SELECT} {where_sql} ORDER BY sc.sno, sc.cno", params
    )
    return jsonify(rows)


@bp.post("/api/enrollments")
@role_required("admin", "student")
def add_enrollment():
    user = current_user()
    body = get_json_body()
    sno = user["related_id"] if user["role"] == "student" else (body.get("sno") or "").strip()
    cno = (body.get("cno") or "").strip()

    if not sno or not cno:
        raise ServiceError("学号和课程号不能为空")

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT sno, status FROM student WHERE sno = %s", (sno,))
        student_row = cursor.fetchone()
        if not student_row:
            raise ServiceError("学生不存在")
        if student_row["status"] != "在读":
            raise ServiceError("只有在读学生可以选课")

        cursor.execute("SELECT cno, status FROM course WHERE cno = %s", (cno,))
        course_row = cursor.fetchone()
        if not course_row:
            raise ServiceError("课程不存在")
        if course_row["status"] != "开课中":
            raise ServiceError("课程未开课，不能选课")

        cursor.execute("SELECT sno FROM sc WHERE sno = %s AND cno = %s", (sno, cno))
        if cursor.fetchone():
            raise ServiceError("该学生已选此课程")

        score = body.get("score")
        cursor.execute(
            "INSERT INTO sc (sno, cno, score) VALUES (%s, %s, %s)",
            (sno, cno, None if score in ("", None) else int(score)),
        )
        record_log(cursor, user["display_name"], "新增选课", f"{sno}-{cno}")

    row = fetch_one(
        f"{_SCORE_SELECT} WHERE sc.sno = %s AND sc.cno = %s", (sno, cno)
    )
    return jsonify({"message": "选课成功", "data": row}), 201


@bp.put("/api/enrollments/<sno>/<cno>")
@role_required("admin", "teacher")
def edit_enrollment(sno, cno):
    user = current_user()
    body = get_json_body()

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            """
            SELECT sc.sno, sc.cno, c.tno
            FROM sc sc JOIN course c ON sc.cno = c.cno
            WHERE sc.sno = %s AND sc.cno = %s
            """,
            (sno, cno),
        )
        row = cursor.fetchone()
        if not row:
            raise ServiceError("选课记录不存在", 404)
        if user["role"] == "teacher" and row["tno"] != user["related_id"]:
            raise ServiceError("只能录入自己授课课程的成绩", 403)

        score = body.get("score")
        cursor.execute(
            "UPDATE sc SET score = %s WHERE sno = %s AND cno = %s",
            (None if score in ("", None) else int(score), sno, cno),
        )
        record_log(cursor, user["display_name"], "录入成绩", f"{sno}-{cno}")

    updated = fetch_one(
        f"{_SCORE_SELECT} WHERE sc.sno = %s AND sc.cno = %s", (sno, cno)
    )
    return jsonify({"message": "成绩已更新", "data": updated})


@bp.delete("/api/enrollments/<sno>/<cno>")
@role_required("admin", "student")
def delete_enrollment(sno, cno):
    user = current_user()
    if user["role"] == "student" and sno != user["related_id"]:
        raise ServiceError("学生只能退选自己的课程", 403)

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            "SELECT sno FROM sc WHERE sno = %s AND cno = %s", (sno, cno)
        )
        if not cursor.fetchone():
            raise ServiceError("选课记录不存在", 404)
        cursor.execute("DELETE FROM sc WHERE sno = %s AND cno = %s", (sno, cno))
        record_log(cursor, user["display_name"], "退选课程", f"{sno}-{cno}")
    return jsonify({"message": "退课成功"})

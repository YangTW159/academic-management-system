from flask import Blueprint, jsonify, request

from campus_system.db import db_cursor, fetch_all
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    record_log,
    role_required,
)
from campus_system.services import get_course_profile

bp = Blueprint("courses", __name__)


@bp.get("/api/courses")
@login_required
def course_list():
    user = current_user()
    keyword = (request.args.get("keyword") or "").strip()
    where_clauses = []
    params = []

    if user["role"] == "teacher":
        where_clauses.append("c.tno = %s")
        params.append(user["related_id"])
    elif user["role"] == "student":
        where_clauses.append(
            "EXISTS (SELECT 1 FROM sc sc1 WHERE sc1.cno = c.cno AND sc1.sno = %s)"
        )
        params.append(user["related_id"])

    if keyword:
        where_clauses.append("(c.cno LIKE %s OR c.cname LIKE %s)")
        like_value = f"%{keyword}%"
        params.extend([like_value, like_value])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    rows = fetch_all(
        f"""
        SELECT
          c.cno, c.cname, c.cperiod, c.credit, c.tno,
          c.schedule_info, c.classroom, c.weeks, c.status,
          t.tname AS teacher_name, COUNT(sc.sno) AS selected_count
        FROM course c
        LEFT JOIN teacher t ON c.tno = t.tno
        LEFT JOIN sc ON c.cno = sc.cno
        {where_sql}
        GROUP BY c.cno, c.cname, c.cperiod, c.credit, c.tno,
                 c.schedule_info, c.classroom, c.weeks, c.status, t.tname
        ORDER BY c.cno
        """,
        params,
    )
    return jsonify(rows)


@bp.get("/api/course-catalog")
@login_required
def course_catalog():
    rows = fetch_all(
        """
        SELECT c.cno, c.cname, c.status, c.schedule_info, c.classroom,
               t.tname AS teacher_name
        FROM course c LEFT JOIN teacher t ON c.tno = t.tno
        ORDER BY c.cno
        """
    )
    return jsonify(rows)


@bp.post("/api/courses")
@role_required("admin")
def add_course():
    user = current_user()
    body = get_json_body()
    cno = (body.get("cno") or "").strip()
    cname = (body.get("cname") or "").strip()
    tno = (body.get("tno") or "").strip()

    if not cno or not cname or not tno:
        raise ServiceError("课程号、课程名、授课教师不能为空")

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            "SELECT cno FROM course WHERE cno = %s OR cname = %s", (cno, cname)
        )
        if cursor.fetchone():
            raise ServiceError("课程号或课程名已存在")
        cursor.execute("SELECT tno FROM teacher WHERE tno = %s", (tno,))
        if not cursor.fetchone():
            raise ServiceError("授课教师不存在")

        cursor.execute(
            """
            INSERT INTO course
              (cno, cname, cperiod, credit, tno, schedule_info, classroom, weeks, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cno, cname,
                body.get("cperiod") or 0,
                body.get("credit") or 0,
                tno,
                body.get("schedule_info") or "",
                body.get("classroom") or "",
                body.get("weeks") or "",
                body.get("status") or "开课中",
            ),
        )
        record_log(cursor, user["display_name"], "新增课程", cno)

    return jsonify({"message": "课程已新增", "data": get_course_profile(cno)}), 201


@bp.put("/api/courses/<cno>")
@role_required("admin")
def edit_course(cno):
    user = current_user()
    body = get_json_body()
    course_row = get_course_profile(cno)
    if not course_row:
        raise ServiceError("课程不存在", 404)

    with db_cursor(commit=True) as (_, cursor):
        next_tno = (body.get("tno") or course_row["tno"]).strip()
        cursor.execute("SELECT tno FROM teacher WHERE tno = %s", (next_tno,))
        if not cursor.fetchone():
            raise ServiceError("授课教师不存在")

        next_status = body.get("status") or course_row["status"]
        cursor.execute(
            """
            UPDATE course SET
              cname = %s, cperiod = %s, credit = %s, tno = %s,
              schedule_info = %s, classroom = %s, weeks = %s, status = %s
            WHERE cno = %s
            """,
            (
                body.get("cname") or course_row["cname"],
                body.get("cperiod") or course_row["cperiod"],
                body.get("credit") or course_row["credit"],
                next_tno,
                body.get("schedule_info") or course_row["schedule_info"],
                body.get("classroom") or course_row["classroom"],
                body.get("weeks") or course_row["weeks"],
                next_status,
                cno,
            ),
        )
        if next_status == "停开":
            cursor.execute("DELETE FROM sc WHERE cno = %s", (cno,))
        record_log(cursor, user["display_name"], "更新课程", cno)

    return jsonify({"message": "课程已更新", "data": get_course_profile(cno)})


@bp.delete("/api/courses/<cno>")
@role_required("admin")
def delete_course(cno):
    user = current_user()
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute("SELECT cno FROM course WHERE cno = %s", (cno,))
        if not cursor.fetchone():
            raise ServiceError("课程不存在", 404)
        cursor.execute("DELETE FROM sc WHERE cno = %s", (cno,))
        cursor.execute("DELETE FROM course WHERE cno = %s", (cno,))
        record_log(cursor, user["display_name"], "删除课程", cno)
    return jsonify({"message": "课程已删除"})

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
from campus_system.models import Course, SC, Student

bp = Blueprint("enrollments", __name__)


def _score_row_to_dict(sc, student, course):
    score = sc.score
    gpa = None
    if score is not None:
        gpa = round(max(score - 50, 0) / 10, 1)
    return {
        "sno": sc.sno, "cno": sc.cno, "score": score,
        "student_name": student.sname if student else None,
        "course_name": course.cname if course else None,
        "gpa_point": gpa,
    }


@bp.get("/api/enrollments")
@login_required
def enrollment_list():
    user = current_user()
    query = db.session.query(SC, Student, Course).join(
        Student, SC.sno == Student.sno
    ).join(Course, SC.cno == Course.cno)

    if user["role"] == "student":
        query = query.filter(SC.sno == user["related_id"])
    elif user["role"] == "teacher":
        query = query.filter(Course.tno == user["related_id"])
    elif user["role"] == "dormManager":
        query = query.filter(False)

    rows = query.order_by(SC.sno, SC.cno).all()
    return jsonify([_score_row_to_dict(sc, s, c) for sc, s, c in rows])


@bp.post("/api/enrollments")
@role_required("admin", "student")
def add_enrollment():
    user = current_user()
    body = get_json_body()
    sno = user["related_id"] if user["role"] == "student" else (body.get("sno") or "").strip()
    cno = (body.get("cno") or "").strip()

    if not sno or not cno:
        raise ServiceError("学号和课程号不能为空")

    student = Student.query.filter_by(sno=sno).first()
    if not student:
        raise ServiceError("学生不存在")
    if student.status != "在读":
        raise ServiceError("只有在读学生可以选课")

    course = Course.query.filter_by(cno=cno).first()
    if not course:
        raise ServiceError("课程不存在")
    if course.status != "开课中":
        raise ServiceError("课程未开课，不能选课")

    if SC.query.filter_by(sno=sno, cno=cno).first():
        raise ServiceError("该学生已选此课程")

    score = body.get("score")
    sc = SC(sno=sno, cno=cno, score=None if score in ("", None) else int(score))
    db.session.add(sc)
    db.session.commit()
    record_log(user["display_name"], "新增选课", f"{sno}-{cno}")

    return jsonify({"message": "选课成功", "data": _score_row_to_dict(sc, student, course)}), 201


@bp.put("/api/enrollments/<sno>/<cno>")
@role_required("admin", "teacher")
def edit_enrollment(sno, cno):
    user = current_user()
    body = get_json_body()

    sc = SC.query.filter_by(sno=sno, cno=cno).first()
    if not sc:
        raise ServiceError("选课记录不存在", 404)

    course = Course.query.filter_by(cno=cno).first()
    if user["role"] == "teacher" and course and course.tno != user["related_id"]:
        raise ServiceError("只能录入自己授课课程的成绩", 403)

    score = body.get("score")
    sc.score = None if score in ("", None) else int(score)
    db.session.commit()
    record_log(user["display_name"], "录入成绩", f"{sno}-{cno}")

    student = Student.query.filter_by(sno=sno).first()
    return jsonify({"message": "成绩已更新", "data": _score_row_to_dict(sc, student, course)})


@bp.delete("/api/enrollments/<sno>/<cno>")
@role_required("admin", "student")
def delete_enrollment(sno, cno):
    user = current_user()
    if user["role"] == "student" and sno != user["related_id"]:
        raise ServiceError("学生只能退选自己的课程", 403)

    sc = SC.query.filter_by(sno=sno, cno=cno).first()
    if not sc:
        raise ServiceError("选课记录不存在", 404)
    db.session.delete(sc)
    db.session.commit()
    record_log(user["display_name"], "退选课程", f"{sno}-{cno}")
    return jsonify({"message": "退课成功"})

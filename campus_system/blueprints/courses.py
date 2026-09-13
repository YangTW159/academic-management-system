from flask import Blueprint, jsonify, request

from campus_system.db import db
from campus_system.extensions import (
    ServiceError,
    current_user,
    get_json_body,
    login_required,
    record_log,
    role_required,
)
from campus_system.models import Course, SC, Teacher
from campus_system.services import get_course_profile

bp = Blueprint("courses", __name__)


@bp.get("/api/courses")
@login_required
def course_list():
    user = current_user()
    keyword = (request.args.get("keyword") or "").strip()

    query = db.session.query(
        Course.cno, Course.cname, Course.cperiod, Course.credit, Course.tno,
        Course.schedule_info, Course.classroom, Course.weeks, Course.status,
        Teacher.tname.label("teacher_name"),
        db.func.count(SC.sno).label("selected_count"),
    ).outerjoin(Teacher, Course.tno == Teacher.tno
    ).outerjoin(SC, Course.cno == SC.cno)

    if user["role"] == "teacher":
        query = query.filter(Course.tno == user["related_id"])
    elif user["role"] == "student":
        query = query.filter(
            db.session.query(SC).filter(SC.cno == Course.cno, SC.sno == user["related_id"]).exists()
        )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(db.or_(Course.cno.like(like), Course.cname.like(like)))

    rows = query.group_by(
        Course.cno, Course.cname, Course.cperiod, Course.credit, Course.tno,
        Course.schedule_info, Course.classroom, Course.weeks, Course.status, Teacher.tname
    ).order_by(Course.cno).all()

    return jsonify([{
        "cno": r.cno, "cname": r.cname, "cperiod": r.cperiod,
        "credit": float(r.credit) if r.credit else 0,
        "tno": r.tno, "schedule_info": r.schedule_info,
        "classroom": r.classroom, "weeks": r.weeks, "status": r.status,
        "teacher_name": r.teacher_name, "selected_count": r.selected_count or 0,
    } for r in rows])


@bp.get("/api/course-catalog")
@login_required
def course_catalog():
    rows = db.session.query(
        Course.cno, Course.cname, Course.status, Course.schedule_info,
        Course.classroom, Teacher.tname.label("teacher_name"),
    ).outerjoin(Teacher, Course.tno == Teacher.tno
    ).order_by(Course.cno).all()
    return jsonify([{
        "cno": r.cno, "cname": r.cname, "status": r.status,
        "schedule_info": r.schedule_info, "classroom": r.classroom,
        "teacher_name": r.teacher_name,
    } for r in rows])


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
    if Course.query.filter((Course.cno == cno) | (Course.cname == cname)).first():
        raise ServiceError("课程号或课程名已存在")
    if not Teacher.query.filter_by(tno=tno).first():
        raise ServiceError("授课教师不存在")

    course = Course(
        cno=cno, cname=cname,
        cperiod=body.get("cperiod") or 0,
        credit=body.get("credit") or 0,
        tno=tno,
        schedule_info=body.get("schedule_info") or "",
        classroom=body.get("classroom") or "",
        weeks=body.get("weeks") or "",
        status=body.get("status") or "开课中",
    )
    db.session.add(course)
    db.session.commit()
    record_log(user["display_name"], "新增课程", cno)

    return jsonify({"message": "课程已新增", "data": get_course_profile(cno)}), 201


@bp.put("/api/courses/<cno>")
@role_required("admin")
def edit_course(cno):
    user = current_user()
    body = get_json_body()
    course_row = get_course_profile(cno)
    if not course_row:
        raise ServiceError("课程不存在", 404)

    next_tno = (body.get("tno") or course_row["tno"]).strip()
    if not Teacher.query.filter_by(tno=next_tno).first():
        raise ServiceError("授课教师不存在")

    course = Course.query.filter_by(cno=cno).first()
    if "cname" in body:
        course.cname = body["cname"]
    if "cperiod" in body:
        course.cperiod = body["cperiod"]
    if "credit" in body:
        course.credit = body["credit"]
    course.tno = next_tno
    if "schedule_info" in body:
        course.schedule_info = body["schedule_info"]
    if "classroom" in body:
        course.classroom = body["classroom"]
    if "weeks" in body:
        course.weeks = body["weeks"]
    next_status = body.get("status") or course_row["status"]
    course.status = next_status

    if next_status == "停开":
        SC.query.filter_by(cno=cno).delete()

    db.session.commit()
    record_log(user["display_name"], "更新课程", cno)
    return jsonify({"message": "课程已更新", "data": get_course_profile(cno)})


@bp.delete("/api/courses/<cno>")
@role_required("admin")
def delete_course(cno):
    user = current_user()
    course = Course.query.filter_by(cno=cno).first()
    if not course:
        raise ServiceError("课程不存在", 404)
    SC.query.filter_by(cno=cno).delete()
    db.session.delete(course)
    db.session.commit()
    record_log(user["display_name"], "删除课程", cno)
    return jsonify({"message": "课程已删除"})

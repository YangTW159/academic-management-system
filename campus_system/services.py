from campus_system.db import db
from campus_system.models import (
    ClassInfo, Course, Dormitory, Notice, OperationLog, SC, Student, Teacher,
)


def build_shortcuts(role):
    if role == "admin":
        return ["维护学生档案", "发布校园通知", "调整宿舍分配", "查看系统日志"]
    if role == "teacher":
        return ["查看授课课程", "录入课程成绩", "追踪课程通知"]
    if role == "student":
        return ["查看个人课表", "查询成绩分析", "确认宿舍信息"]
    return ["维护宿舍信息", "查看床位情况", "发布宿舍通知"]


def get_course_profile(cno):
    row = db.session.query(
        Course.cno, Course.cname, Course.cperiod, Course.credit, Course.tno,
        Course.schedule_info, Course.classroom, Course.weeks, Course.status,
        Teacher.tname.label("teacher_name"),
        db.func.count(SC.sno).label("selected_count"),
    ).outerjoin(Teacher, Course.tno == Teacher.tno
    ).outerjoin(SC, Course.cno == SC.cno
    ).filter(Course.cno == cno
    ).group_by(
        Course.cno, Course.cname, Course.cperiod, Course.credit, Course.tno,
        Course.schedule_info, Course.classroom, Course.weeks, Course.status, Teacher.tname
    ).first()
    if not row:
        return None
    return {
        "cno": row.cno, "cname": row.cname, "cperiod": row.cperiod,
        "credit": float(row.credit) if row.credit else 0,
        "tno": row.tno, "schedule_info": row.schedule_info,
        "classroom": row.classroom, "weeks": row.weeks, "status": row.status,
        "teacher_name": row.teacher_name, "selected_count": row.selected_count or 0,
    }


def get_visible_notices(user, keyword=""):
    query = Notice.query.order_by(Notice.pinned.desc(), Notice.publish_time.desc())
    rows = query.all()

    student_class_name = ""
    if user["role"] == "student":
        student = Student.query.filter_by(sno=user["related_id"]).first()
        if student:
            cls = ClassInfo.query.filter_by(class_id=student.class_id).first()
            student_class_name = cls.class_name if cls else ""

    buildings = []
    if user["role"] == "dormManager":
        buildings = [d.building + "栋" for d in Dormitory.query.filter_by(dm_id=user["related_id"]).all()]

    keyword = (keyword or "").strip()
    visible = []
    for row in rows:
        scope = row.scope or ""
        if user["role"] == "admin":
            allowed = True
        elif user["role"] == "student":
            allowed = scope in {"全校", "全员", "在读学生", student_class_name}
        elif user["role"] == "teacher":
            allowed = scope in {"全校", "全员", "教师"} or row.publisher_role == "teacher"
        elif user["role"] == "dormManager":
            allowed = scope in {"全校", "全员", "宿管"} or scope in buildings
        else:
            allowed = False

        if not allowed:
            continue
        if keyword and keyword not in row.title and keyword not in row.content:
            continue
        visible.append(row.to_dict())
    return visible


def get_dashboard_payload(user):
    total_students = Student.query.count()
    active_students = Student.query.filter_by(status="在读").count()
    total_courses = Course.query.count()
    open_courses = Course.query.filter_by(status="开课中").count()
    total_dorms = Dormitory.query.count()
    total_max = db.session.query(db.func.sum(Dormitory.max_num)).scalar() or 0
    total_cur = db.session.query(db.func.sum(Dormitory.cur_num)).scalar() or 0
    bed_usage_rate = round(total_cur / total_max * 100, 1) if total_max else 0
    total_notices = Notice.query.count()

    summary = {
        "total_students": total_students,
        "active_students": active_students,
        "total_courses": total_courses,
        "open_courses": open_courses,
        "total_dorms": total_dorms,
        "bed_usage_rate": bed_usage_rate,
        "total_notices": total_notices,
    }

    class_rows = db.session.query(
        ClassInfo.class_name.label("label"),
        db.func.count(Student.sno).label("value"),
    ).outerjoin(Student, ClassInfo.class_id == Student.class_id
    ).group_by(ClassInfo.class_id, ClassInfo.class_name
    ).order_by(ClassInfo.class_id).all()

    course_score_rows = db.session.query(
        Course.cname.label("label"),
        db.func.round(db.func.avg(SC.score), 1).label("value"),
    ).outerjoin(SC, Course.cno == SC.cno
    ).group_by(Course.cno, Course.cname).order_by(Course.cno).all()

    notice_rows = db.session.query(
        Notice.category.label("label"),
        db.func.count(Notice.nid).label("value"),
    ).group_by(Notice.category).order_by(db.func.count(Notice.nid).desc(), Notice.category).all()

    latest_notices = get_visible_notices(user)[:5]

    if user["role"] == "admin":
        recent_logs = OperationLog.query.order_by(OperationLog.log_id.desc()).limit(8).all()
    else:
        recent_logs = OperationLog.query.filter_by(actor=user["display_name"]).order_by(
            OperationLog.log_id.desc()
        ).limit(8).all()

    return {
        "summary": summary,
        "charts": {
            "class_distribution": [{"label": r.label, "value": r.value} for r in class_rows],
            "course_scores": [{"label": r.label, "value": float(r.value or 0)} for r in course_score_rows],
            "notice_stats": [{"label": r.label, "value": r.value} for r in notice_rows],
        },
        "latest_notices": latest_notices,
        "recent_logs": [r.to_dict() for r in recent_logs],
        "shortcuts": build_shortcuts(user["role"]),
    }

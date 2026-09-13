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
from campus_system.models import ClassInfo, Course, Dormitory, SC, Student, Teacher

bp = Blueprint("students", __name__)


# ---------- 基础数据下拉 ----------
@bp.get("/api/classes")
@login_required
def classes():
    rows = ClassInfo.query.order_by(ClassInfo.class_id).all()
    return jsonify([r.to_dict() for r in rows])


@bp.get("/api/teachers")
@login_required
def teachers():
    rows = Teacher.query.order_by(Teacher.tno).all()
    return jsonify([r.to_dict() for r in rows])


@bp.get("/api/dorm-managers")
@login_required
def dorm_managers():
    from campus_system.models import DormManager
    rows = DormManager.query.order_by(DormManager.dm_id).all()
    return jsonify([r.to_dict() for r in rows])


# ---------- 学生 CRUD ----------
@bp.get("/api/students")
@login_required
def student_list():
    user = current_user()
    keyword = (request.args.get("keyword") or "").strip()

    query = db.session.query(
        Student.sno, Student.sname, Student.sgender,
        Student.sbirth, Student.sphone, Student.class_id,
        Student.dorm_id, Student.status,
        ClassInfo.class_name, ClassInfo.major, ClassInfo.college,
        Dormitory.building, Dormitory.room,
    ).outerjoin(ClassInfo, Student.class_id == ClassInfo.class_id
    ).outerjoin(Dormitory, Student.dorm_id == Dormitory.dorm_id)

    if user["role"] == "student":
        query = query.filter(Student.sno == user["related_id"])
    elif user["role"] == "dormManager":
        query = query.filter(Dormitory.dm_id == user["related_id"])
    elif user["role"] == "teacher":
        query = query.filter(
            db.session.query(SC).join(Course, SC.cno == Course.cno).filter(
                SC.sno == Student.sno, Course.tno == user["related_id"]
            ).exists()
        )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(Student.sno.like(like), Student.sname.like(like), ClassInfo.class_name.like(like))
        )

    rows = query.order_by(Student.sno).all()
    result = []
    for r in rows:
        result.append({
            "sno": r.sno, "sname": r.sname, "sgender": r.sgender,
            "sbirth": r.sbirth.isoformat() if r.sbirth else None,
            "sphone": r.sphone, "class_id": r.class_id, "dorm_id": r.dorm_id,
            "status": r.status, "class_name": r.class_name, "major": r.major,
            "college": r.college,
            "dorm_summary": f"{r.building}-{r.room}" if r.building else "未分配",
        })
    return jsonify(result)


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

    if Student.query.filter_by(sno=sno).first():
        raise ServiceError("学号已存在")
    if not ClassInfo.query.filter_by(class_id=class_id).first():
        raise ServiceError("班级不存在")

    dorm = None
    if dorm_id:
        dorm = Dormitory.query.filter_by(dorm_id=dorm_id).first()
        if not dorm:
            raise ServiceError("宿舍不存在")
        if dorm.cur_num >= dorm.max_num:
            raise ServiceError("宿舍床位已满，无法分配")

    student = Student(
        sno=sno, sname=sname,
        sgender=body.get("sgender") or None,
        sbirth=body.get("sbirth") or None,
        sphone=body.get("sphone") or None,
        class_id=class_id, dorm_id=dorm_id, status=status,
    )
    db.session.add(student)

    if dorm and status not in {"退学", "毕业"}:
        dorm.cur_num += 1

    db.session.commit()
    record_log(user["display_name"], "新增学生", sno)

    profile = get_student_profile(sno)
    return jsonify({"message": "学生信息已新增", "data": profile}), 201


@bp.put("/api/students/<sno>")
@role_required("admin")
def edit_student(sno):
    user = current_user()
    body = get_json_body()

    student = Student.query.filter_by(sno=sno).first()
    if not student:
        raise ServiceError("学生不存在", 404)

    next_dorm_id = (body.get("dorm_id") if "dorm_id" in body else student.dorm_id) or None
    next_status = (body.get("status") if "status" in body else student.status) or student.status
    old_dorm_id = student.dorm_id

    if "class_id" in body:
        if not ClassInfo.query.filter_by(class_id=body["class_id"]).first():
            raise ServiceError("班级不存在")

    if next_dorm_id and next_dorm_id != old_dorm_id and next_status not in {"退学", "毕业"}:
        new_dorm = Dormitory.query.filter_by(dorm_id=next_dorm_id).first()
        if not new_dorm:
            raise ServiceError("目标宿舍不存在")
        if new_dorm.cur_num >= new_dorm.max_num:
            raise ServiceError("目标宿舍已满")

    # 更新学生字段
    if "sname" in body:
        student.sname = body["sname"]
    if "sgender" in body:
        student.sgender = body["sgender"] or None
    if "sbirth" in body:
        student.sbirth = body["sbirth"] or None
    if "sphone" in body:
        student.sphone = body["sphone"] or None
    if "class_id" in body:
        student.class_id = body["class_id"]
    student.status = next_status
    student.dorm_id = None if next_status in {"退学", "毕业"} else next_dorm_id

    # 处理宿舍人数变动
    final_dorm_id = None if next_status in {"退学", "毕业"} else next_dorm_id
    if old_dorm_id and old_dorm_id != final_dorm_id:
        old_dorm = Dormitory.query.filter_by(dorm_id=old_dorm_id).first()
        if old_dorm:
            old_dorm.cur_num = max(old_dorm.cur_num - 1, 0)
    if final_dorm_id and final_dorm_id != old_dorm_id and next_status not in {"退学", "毕业"}:
        new_dorm = Dormitory.query.filter_by(dorm_id=final_dorm_id).first()
        if new_dorm:
            new_dorm.cur_num += 1

    db.session.commit()
    record_log(user["display_name"], "更新学生", sno)

    return jsonify({"message": "学生信息已更新", "data": get_student_profile(sno)})


@bp.delete("/api/students/<sno>")
@role_required("admin")
def delete_student(sno):
    user = current_user()
    student = Student.query.filter_by(sno=sno).first()
    if not student:
        raise ServiceError("学生不存在", 404)

    if student.dorm_id:
        dorm = Dormitory.query.filter_by(dorm_id=student.dorm_id).first()
        if dorm:
            dorm.cur_num = max(dorm.cur_num - 1, 0)

    SC.query.filter_by(sno=sno).delete()
    db.session.delete(student)
    db.session.commit()
    record_log(user["display_name"], "删除学生", sno)
    return jsonify({"message": "学生信息已删除"})


def get_student_profile(sno):
    """返回学生详情（含班级和宿舍信息）。"""
    row = db.session.query(
        Student.sno, Student.sname, Student.sgender, Student.sbirth,
        Student.sphone, Student.class_id, Student.dorm_id, Student.status,
        ClassInfo.class_name, ClassInfo.major, ClassInfo.college,
        Dormitory.building, Dormitory.room,
    ).outerjoin(ClassInfo, Student.class_id == ClassInfo.class_id
    ).outerjoin(Dormitory, Student.dorm_id == Dormitory.dorm_id
    ).filter(Student.sno == sno).first()

    if not row:
        return None
    return {
        "sno": row.sno, "sname": row.sname, "sgender": row.sgender,
        "sbirth": row.sbirth.isoformat() if row.sbirth else None,
        "sphone": row.sphone, "class_id": row.class_id, "dorm_id": row.dorm_id,
        "status": row.status, "class_name": row.class_name, "major": row.major,
        "college": row.college,
        "dorm_summary": f"{row.building}-{row.room}" if row.building else "未分配",
    }

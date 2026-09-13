"""ORM 模型：对应 edu 库的 10 张业务表。"""
from datetime import datetime

from campus_system.db import db


class SysUser(db.Model):
    __tablename__ = "sys_user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role_name = db.Column(db.String(20), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    related_id = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role_name": self.role_name,
            "display_name": self.display_name,
            "related_id": self.related_id,
            "status": self.status,
        }


class ClassInfo(db.Model):
    __tablename__ = "class_info"
    class_id = db.Column(db.String(20), primary_key=True)
    class_name = db.Column(db.String(50), unique=True, nullable=False)
    major = db.Column(db.String(80), nullable=False)
    college = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "major": self.major,
            "college": self.college,
        }


class Teacher(db.Model):
    __tablename__ = "teacher"
    tno = db.Column(db.String(20), primary_key=True)
    tname = db.Column(db.String(50), nullable=False)
    tgender = db.Column(db.String(10), nullable=True)
    tedu = db.Column(db.String(30), nullable=True)
    tpro = db.Column(db.String(30), nullable=True)

    courses = db.relationship("Course", backref="teacher", lazy=True)

    def to_dict(self):
        return {
            "tno": self.tno,
            "tname": self.tname,
            "tgender": self.tgender,
            "tedu": self.tedu,
            "tpro": self.tpro,
        }


class Course(db.Model):
    __tablename__ = "course"
    cno = db.Column(db.String(20), primary_key=True)
    cname = db.Column(db.String(100), unique=True, nullable=False)
    cperiod = db.Column(db.Integer, nullable=False, default=0)
    credit = db.Column(db.Numeric(4, 1), nullable=False, default=0)
    tno = db.Column(db.String(20), db.ForeignKey("teacher.tno"), nullable=False)
    schedule_info = db.Column(db.String(100), nullable=False, default="")
    classroom = db.Column(db.String(50), nullable=False, default="")
    weeks = db.Column(db.String(50), nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="开课中")

    def to_dict(self):
        return {
            "cno": self.cno,
            "cname": self.cname,
            "cperiod": self.cperiod,
            "credit": float(self.credit) if self.credit is not None else 0,
            "tno": self.tno,
            "schedule_info": self.schedule_info,
            "classroom": self.classroom,
            "weeks": self.weeks,
            "status": self.status,
        }


class DormManager(db.Model):
    __tablename__ = "dorm_manager"
    dm_id = db.Column(db.String(20), primary_key=True)
    dm_name = db.Column(db.String(50), nullable=False)
    dm_gender = db.Column(db.String(10), nullable=True)
    dm_phone = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "dm_id": self.dm_id,
            "dm_name": self.dm_name,
            "dm_gender": self.dm_gender,
            "dm_phone": self.dm_phone,
        }


class Dormitory(db.Model):
    __tablename__ = "dormitory"
    dorm_id = db.Column(db.String(20), primary_key=True)
    building = db.Column(db.String(30), nullable=False)
    room = db.Column(db.String(20), nullable=False)
    max_num = db.Column(db.Integer, nullable=False, default=4)
    cur_num = db.Column(db.Integer, nullable=False, default=0)
    dm_id = db.Column(db.String(20), db.ForeignKey("dorm_manager.dm_id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="正常")

    def to_dict(self):
        return {
            "dorm_id": self.dorm_id,
            "building": self.building,
            "room": self.room,
            "max_num": self.max_num,
            "cur_num": self.cur_num,
            "dm_id": self.dm_id,
            "status": self.status,
        }


class Student(db.Model):
    __tablename__ = "student"
    sno = db.Column(db.String(20), primary_key=True)
    sname = db.Column(db.String(50), nullable=False)
    sgender = db.Column(db.String(10), nullable=True)
    sbirth = db.Column(db.Date, nullable=True)
    sphone = db.Column(db.String(20), nullable=True)
    class_id = db.Column(db.String(20), db.ForeignKey("class_info.class_id"), nullable=False)
    dorm_id = db.Column(db.String(20), db.ForeignKey("dormitory.dorm_id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="在读")

    class_info = db.relationship("ClassInfo", backref="students")
    dormitory = db.relationship("Dormitory", backref="students")

    def to_dict(self):
        return {
            "sno": self.sno,
            "sname": self.sname,
            "sgender": self.sgender,
            "sbirth": self.sbirth.isoformat() if self.sbirth else None,
            "sphone": self.sphone,
            "class_id": self.class_id,
            "dorm_id": self.dorm_id,
            "status": self.status,
        }


class SC(db.Model):
    __tablename__ = "sc"
    sno = db.Column(db.String(20), db.ForeignKey("student.sno"), primary_key=True)
    cno = db.Column(db.String(20), db.ForeignKey("course.cno"), primary_key=True)
    score = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {"sno": self.sno, "cno": self.cno, "score": self.score}


class Notice(db.Model):
    __tablename__ = "notice"
    nid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    publisher = db.Column(db.String(50), nullable=False)
    publisher_role = db.Column(db.String(20), nullable=False)
    scope = db.Column(db.String(50), nullable=False, default="全校")
    category = db.Column(db.String(30), nullable=False, default="学校")
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default="已发布")

    def to_dict(self):
        return {
            "nid": self.nid,
            "title": self.title,
            "content": self.content,
            "publish_time": self.publish_time.strftime("%Y-%m-%d %H:%M") if self.publish_time else None,
            "publisher": self.publisher,
            "publisher_role": self.publisher_role,
            "scope": self.scope,
            "category": self.category,
            "pinned": self.pinned,
            "status": self.status,
        }


class OperationLog(db.Model):
    __tablename__ = "operation_log"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actor = db.Column(db.String(50), nullable=False)
    action_name = db.Column(db.String(50), nullable=False)
    target_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "actor": self.actor,
            "action_name": self.action_name,
            "target_name": self.target_name,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

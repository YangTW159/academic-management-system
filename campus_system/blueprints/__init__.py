"""Blueprint 注册入口。"""
from flask import Flask

from campus_system.blueprints.auth import bp as auth_bp
from campus_system.blueprints.dashboard import bp as dashboard_bp
from campus_system.blueprints.students import bp as students_bp
from campus_system.blueprints.courses import bp as courses_bp
from campus_system.blueprints.dormitories import bp as dormitories_bp
from campus_system.blueprints.notices import bp as notices_bp
from campus_system.blueprints.enrollments import bp as enrollments_bp
from campus_system.blueprints.logs import bp as logs_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(dormitories_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(enrollments_bp)
    app.register_blueprint(logs_bp)

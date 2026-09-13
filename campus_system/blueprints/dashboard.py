from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from campus_system.config import APP_CONFIG
from campus_system.db import db
from campus_system.extensions import current_user, login_required
from campus_system.services import get_dashboard_payload

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    return render_template("index.html", app_name=APP_CONFIG["APP_NAME"])


@bp.get("/api/health")
def health():
    version = db.session.execute(text("SELECT VERSION() AS version")).scalar()
    return jsonify({"message": "数据库连接正常", "version": version})


@bp.get("/api/dashboard")
@login_required
def dashboard():
    return jsonify(get_dashboard_payload(current_user()))

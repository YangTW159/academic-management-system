from flask import Blueprint, jsonify, render_template

from campus_system.config import APP_CONFIG
from campus_system.db import fetch_one
from campus_system.extensions import current_user, login_required
from campus_system.services import get_dashboard_payload

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    return render_template("index.html", app_name=APP_CONFIG["APP_NAME"])


@bp.get("/api/health")
def health():
    row = fetch_one("SELECT VERSION() AS version")
    return jsonify({"message": "数据库连接正常", "version": row["version"]})


@bp.get("/api/dashboard")
@login_required
def dashboard():
    return jsonify(get_dashboard_payload(current_user()))

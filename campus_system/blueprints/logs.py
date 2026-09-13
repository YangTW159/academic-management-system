from flask import Blueprint, jsonify

from campus_system.db import fetch_all
from campus_system.extensions import role_required

bp = Blueprint("logs", __name__)


@bp.get("/api/logs")
@role_required("admin")
def operation_logs():
    rows = fetch_all(
        """
        SELECT log_id, actor, action_name, target_name,
               DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
        FROM operation_log ORDER BY log_id DESC
        """
    )
    return jsonify(rows)

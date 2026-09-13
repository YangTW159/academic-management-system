from flask import Blueprint, jsonify

from campus_system.extensions import role_required
from campus_system.models import OperationLog

bp = Blueprint("logs", __name__)


@bp.get("/api/logs")
@role_required("admin")
def operation_logs():
    rows = OperationLog.query.order_by(OperationLog.log_id.desc()).all()
    return jsonify([r.to_dict() for r in rows])

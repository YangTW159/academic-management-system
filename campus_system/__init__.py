"""应用工厂：create_app() 返回配置好的 Flask 实例。"""
import logging

from flask import Flask, jsonify
from pymysql import MySQLError

from campus_system.config import APP_CONFIG
from campus_system.extensions import ServiceError
from campus_system.blueprints import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = APP_CONFIG["SECRET_KEY"]

    # 日志：控制台输出，生产可替换为 FileHandler / RotatingFileHandler
    logging.basicConfig(
        level=logging.INFO if APP_CONFIG["DEBUG"] else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    register_blueprints(app)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ServiceError)
    def _handle_service_error(error: ServiceError):
        return jsonify({"message": error.message}), error.status_code

    @app.errorhandler(MySQLError)
    def _handle_db_error(error: MySQLError):
        return (
            jsonify({
                "message": "数据库连接或 SQL 执行失败，请检查 MySQL 配置",
                "detail": str(error),
            }),
            500,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected_error(error: Exception):
        app.logger.exception("unhandled error: %s", error)
        return jsonify({"message": "系统内部错误", "detail": str(error)}), 500

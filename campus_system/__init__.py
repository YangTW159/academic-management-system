"""应用工厂：create_app() 返回配置好的 Flask 实例。"""
import logging

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from pymysql import MySQLError

from campus_system.config import APP_CONFIG, SQLALCHEMY_DATABASE_URI, JWT_SECRET_KEY, REDIS_URL
from campus_system.db import db
from campus_system.extensions import ServiceError
from campus_system.cache import init_redis
from campus_system.blueprints import register_blueprints


SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "校园教务综合管理系统 API",
        "description": "Flask + SQLAlchemy + JWT 后端接口文档",
        "version": "1.0",
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "输入: Bearer <access_token>",
        }
    },
}


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = APP_CONFIG["SECRET_KEY"]

    # SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # JWT
    app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
    JWTManager(app)

    # Swagger
    app.config["SWAGGER"] = {"title": "教务系统 API", "uiversion": 3}
    Swagger(app, template=SWAGGER_TEMPLATE)

    # Redis 缓存（可选）
    app.config["REDIS_URL"] = REDIS_URL
    init_redis(app)

    # 日志
    logging.basicConfig(
        level=logging.INFO if APP_CONFIG["DEBUG"] else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    register_blueprints(app)
    _register_error_handlers(app)

    # 导入模型，确保表被识别
    with app.app_context():
        from campus_system import models  # noqa: F401

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

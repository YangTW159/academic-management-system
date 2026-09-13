"""生产入口：python wsgi.py 启动开发服务；生产建议用 waitress/gunicorn。"""
from campus_system import create_app
from campus_system.config import APP_CONFIG

app = create_app()

if __name__ == "__main__":
    app.run(
        host=APP_CONFIG["HOST"],
        port=APP_CONFIG["PORT"],
        debug=APP_CONFIG["DEBUG"],
    )

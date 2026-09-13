import os
from pathlib import Path


def load_dotenv():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()


APP_CONFIG = {
    "APP_NAME": "校园综合事务管理系统",
    "HOST": os.getenv("HOST", "127.0.0.1"),
    "PORT": int(os.getenv("PORT", "5000")),
    "SECRET_KEY": os.getenv("SECRET_KEY", "change-me-in-production"),
    "DEBUG": os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"},
}

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "edu"),
    "charset": "utf8mb4",
    "autocommit": False,
}

# SQLAlchemy 连接串
SQLALCHEMY_DATABASE_URI = (
    "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}".format(
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
    )
)

# JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", APP_CONFIG["SECRET_KEY"])

# Redis 配置（可选，不配置则降级不用缓存）
REDIS_URL = os.getenv("REDIS_URL", "")

ROLE_LABELS = {
    "admin": "管理员",
    "teacher": "教师",
    "student": "学生",
    "dormManager": "宿管",
}

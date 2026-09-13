# 校园教务综合管理系统

Flask + SQLAlchemy + JWT + MySQL 的教务管理后台，支持学生/课程/宿舍/公告/选课/日志六大业务模块。

## 技术栈

- **后端**：Flask 3 + Flask-SQLAlchemy（ORM）+ Flask-JWT-Extended（鉴权）
- **数据库**：MySQL 8.0（10 张业务表）
- **缓存/异步**：Redis（接口缓存，可选）+ Celery（批量发通知异步任务）
- **接口文档**：Flasgger（Swagger UI）
- **测试**：pytest（12 个用例）
- **部署**：waitress（Windows）/ gunicorn（Linux）+ Nginx

## 项目结构

```
campus_system/
├── __init__.py          # 应用工厂 + 错误处理 + Swagger/Redis/JWT 初始化
├── config.py            # 配置（从 .env 读取）
├── db.py                # SQLAlchemy 实例
├── models.py            # ORM 模型（10 张表）
├── cache.py             # Redis 缓存层（可选，未连接自动降级）
├── tasks.py             # Celery 异步任务（批量发通知）
├── extensions.py        # 鉴权装饰器 + 业务异常
├── services.py          # 业务逻辑层
└── blueprints/          # 8 个蓝图模块
    ├── auth.py          # 登录/登出（返回 JWT token）
    ├── dashboard.py     # 首页 + health
    ├── students.py      # 学生 CRUD
    ├── courses.py       # 课程 CRUD
    ├── dormitories.py   # 宿舍管理
    ├── notices.py       # 公告管理
    ├── enrollments.py   # 选课/成绩
    └── logs.py          # 操作日志
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env（参考 .env.example）
cp .env.example .env
# 修改数据库密码、JWT_SECRET_KEY

# 3. 初始化数据库（确保 MySQL 已建 edu 库，表结构见 SQL 脚本）

# 4. 运行
python wsgi.py

# 5. 访问
# 前端:    http://127.0.0.1:5000
# Swagger: http://127.0.0.1:5000/apidocs/
```

## 测试

```bash
pytest -q
# 12 passed
```

## API 概览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | /api/login | 登录，返回 JWT token |
| 认证 | POST | /api/logout | 登出 |
| 学生 | GET/POST/PUT/DELETE | /api/students | 学生 CRUD |
| 课程 | GET/POST/PUT/DELETE | /api/courses | 课程 CRUD |
| 宿舍 | GET/POST/PUT | /api/dormitories | 宿舍管理 |
| 公告 | GET/POST/PUT/DELETE | /api/notices | 公告管理 |
| 选课 | GET/POST/PUT/DELETE | /api/enrollments | 选课/成绩 |
| 仪表板 | GET | /api/dashboard | 统计数据 |
| 日志 | GET | /api/logs | 操作日志（admin） |

## 生产部署（Linux + Nginx + Gunicorn）

```bash
# 1. 安装 Redis
sudo apt install redis-server

# 2. 用 gunicorn 跑（替代 waitress）
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 "campus_system:create_app()"

# 3. Nginx 反代
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}

# 4. 启动 Celery worker（异步任务）
celery -A campus_system.tasks worker --loglevel=info
```

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |
| 教师 | t001 | 123456 |
| 学生 | s2024001 | 123456 |
| 宿管 | dm01 | 123456 |

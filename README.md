# 校园综合事务管理系统（Flask 工程化版）

## 技术栈
- Python 3.10+ / Flask 3.x
- MySQL 8（PyMySQL，参数化查询防注入）
- Flask Blueprint 按业务模块拆分路由
- Session + 装饰器实现 RBAC（admin / teacher / student / dormManager）
- 结构化日志、全局异常处理、.env 配置分离
- pytest 冒烟测试、waitress 生产 WSGI 服务器

## 目录结构
```
.
├── campus_system/           # 应用包
│   ├── __init__.py          # create_app 工厂 + 错误处理 + 日志
│   ├── config.py            # 配置（读 .env）
│   ├── db.py                # PyMySQL 上下文管理器
│   ├── extensions.py        # ServiceError / 登录鉴权装饰器
│   ├── services.py          # 业务查询函数
│   └── blueprints/          # 按模块拆分的路由
│       ├── auth.py          # 登录 / 登出 / 当前会话
│       ├── dashboard.py     # 首页 / 健康检查 / 仪表盘
│       ├── students.py      # 学生 CRUD + 班级/教师/宿管下拉
│       ├── courses.py       # 课程 CRUD
│       ├── dormitories.py   # 宿舍 CRUD
│       ├── notices.py       # 公告 CRUD
│       ├── enrollments.py   # 选课与成绩
│       └── logs.py          # 操作日志
├── static/  templates/      # 前端
├── tests/                   # pytest 冒烟测试
├── wsgi.py                  # 启动入口
├── requirements.txt
└── .env.example
```

## 快速开始
```bash
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
# 编辑 .env 填入 MySQL 账号密码
python wsgi.py
# 浏览器打开 http://127.0.0.1:5000
```

## 生产启动（waitress）
```bash
waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
```

## 测试
```bash
pytest -q
```

## 与旧版 app.py 的关系
- `app_legacy.py` 是原始单文件版本，保留备查。
- 新版通过蓝图拆分，行为与旧版完全一致；如遇问题可直接 `python app_legacy.py` 切回。

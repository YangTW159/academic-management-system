"""冒烟测试：不连数据库，只验证应用工厂能创建、路由能注册。"""
from campus_system import create_app


def test_create_app():
    app = create_app()
    assert app.name == "campus_system"


def test_routes_registered():
    app = create_app()
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert "/" in rules
    assert "/api/login" in rules
    assert "/api/students" in rules
    assert "/api/courses" in rules
    assert "/api/dormitories" in rules
    assert "/api/notices" in rules
    assert "/api/enrollments" in rules
    assert "/api/logs" in rules


def test_service_error_mapping():
    from campus_system.extensions import ServiceError
    app = create_app()
    with app.test_client() as client:
        # 未登录访问受保护接口，应返回 401
        resp = client.get("/api/dashboard")
        assert resp.status_code == 401

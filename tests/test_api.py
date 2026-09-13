"""API 集成测试：连真实数据库，验证登录与主要接口。"""
import pytest

from campus_system import create_app
from campus_system.db import db


@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "数据库连接正常"
    assert "version" in data


def test_login_wrong_password(client):
    resp = client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert "用户名或密码错误" in resp.get_json()["message"]


def test_login_success_returns_token(client):
    resp = client.post("/api/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["display_name"] == "系统管理员"


def test_protected_requires_auth(client):
    client.post("/api/logout")  # 清掉前面测试留下的 session
    resp = client.get("/api/students")
    assert resp.status_code == 401


def test_students_with_session(client):
    client.post("/api/login", json={"username": "admin", "password": "123456"})
    resp = client.get("/api/students")
    assert resp.status_code == 200
    rows = resp.get_json()
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert "sno" in rows[0]
    assert "class_name" in rows[0]


def test_dashboard_with_session(client):
    client.post("/api/login", json={"username": "admin", "password": "123456"})
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "summary" in data
    assert "charts" in data
    assert data["summary"]["total_students"] > 0


def test_jwt_token_access(client):
    login_resp = client.post("/api/login", json={"username": "admin", "password": "123456"})
    token = login_resp.get_json()["access_token"]
    resp = client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_notices_list(client):
    client.post("/api/login", json={"username": "admin", "password": "123456"})
    resp = client.get("/api/notices")
    assert resp.status_code == 200


def test_courses_list(client):
    client.post("/api/login", json={"username": "admin", "password": "123456"})
    resp = client.get("/api/courses")
    assert resp.status_code == 200

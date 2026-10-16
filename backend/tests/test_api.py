import os
from unittest.mock import Mock

os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def database():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def create(client, **overrides):
    return client.post(
        "/api/tickets",
        json={
            "subject": "Cannot access payroll",
            "requester_email": "ada@example.com",
            **overrides,
        },
    )


def test_health_and_readiness(client):
    assert client.get("/health").json() == {"status": "UP"}
    assert client.get("/ready").json() == {"status": "READY"}
    assert client.get("/").json()["service"] == "ResolveDesk API"


def test_create_read_update_delete(client):
    response = create(client)
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["status"] == "OPEN"
    assert ticket["assignee"] == "Unassigned"
    assert ticket["created_at"] and ticket["updated_at"]
    path = f"/api/tickets/{ticket['id']}"
    assert client.get(path).json() == ticket
    updated = client.put(path, json={"status": "IN_PROGRESS", "assignee": "Sam"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "IN_PROGRESS"
    assert updated.json()["subject"] == ticket["subject"]
    assert updated.json()["updated_at"] >= ticket["updated_at"]
    assert (
        client.patch(path, json={"status": "RESOLVED"}).json()["status"] == "RESOLVED"
    )
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"subject": " "},
        {"subject": "x" * 201},
        {"requester_email": "invalid"},
        {"priority": "SUPER"},
        {"status": "DONE"},
        {"assignee": ""},
        {"description": "x" * 10001},
        {"unknown_field": True},
    ],
)
def test_create_validation(client, payload):
    assert create(client, **payload).status_code == 422
    assert client.get("/api/tickets").json() == []


@pytest.mark.parametrize(
    "field",
    ["subject", "description", "requester_email", "priority", "status", "assignee"],
)
def test_update_rejects_explicit_null(client, field):
    ticket = create(client).json()
    response = client.put(f"/api/tickets/{ticket['id']}", json={field: None})
    assert response.status_code == 422
    assert client.get(f"/api/tickets/{ticket['id']}").json() == ticket


@pytest.mark.parametrize(
    "method,payload", [("get", None), ("delete", None), ("put", {"status": "RESOLVED"})]
)
def test_missing_ticket(client, method, payload):
    response = client.request(method, "/api/tickets/999", json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}


def test_search_filters_and_pagination(client):
    first = create(client, subject="VPN login broken", priority="URGENT").json()
    second = create(
        client, subject="New laptop", status="RESOLVED", description="Needs VPN client"
    ).json()
    create(client, subject="Payroll permissions", requester_email="grace@example.com")
    assert len(client.get("/api/tickets?search=vpn").json()) == 2
    assert len(client.get("/api/tickets?search=grace").json()) == 1
    assert client.get("/api/tickets?search=%25").json() == []
    assert client.get("/api/tickets?priority=URGENT&status=OPEN").json() == [first]
    assert client.get("/api/tickets?limit=1&offset=1").json() == [second]
    assert client.get("/api/tickets?limit=501").status_code == 422
    assert client.get("/api/tickets?status=BAD").status_code == 422


def test_stats_only_count_unresolved_urgent(client):
    assert client.get("/api/tickets/stats").json() == {
        "total": 0,
        "open": 0,
        "inProgress": 0,
        "resolved": 0,
        "urgent": 0,
    }
    create(client, priority="URGENT")
    create(client, status="IN_PROGRESS", priority="HIGH")
    create(client, status="RESOLVED", priority="URGENT")
    assert client.get("/api/tickets/stats").json() == {
        "total": 3,
        "open": 1,
        "inProgress": 1,
        "resolved": 1,
        "urgent": 1,
    }


def test_database_failure_is_not_ready(client):
    failed_session = Mock()
    failed_session.execute.side_effect = OperationalError(
        "select", {}, RuntimeError("private database error")
    )
    app.dependency_overrides[get_db] = lambda: failed_session
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert client.get("/health").status_code == 200


def test_metrics_exposed(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text

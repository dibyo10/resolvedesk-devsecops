import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def request(base, method, path, payload=None, expected=200):
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=15) as response:
            status, content = response.status, response.read()
    except HTTPError as error:
        status, content = error.code, error.read()
    assert status == expected, (
        f"{method} {path}: expected {expected}, got {status}: {content[:300]!r}"
    )
    return json.loads(content) if content else None


def main():
    parser = argparse.ArgumentParser(
        description="Exercise ResolveDesk HTTP endpoints using synthetic tickets."
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--persist-state", type=Path)
    parser.add_argument("--verify-state", type=Path)
    args = parser.parse_args()
    assert not (args.persist_state and args.verify_state), (
        "Choose one persistence operation"
    )
    base = args.base_url
    assert request(base, "GET", "/health") == {"status": "UP"}
    assert request(base, "GET", "/ready") == {"status": "READY"}
    if args.verify_state:
        saved = json.loads(args.verify_state.read_text())
        ticket = request(base, "GET", f"/api/tickets/{saved['id']}")
        assert ticket["subject"] == saved["subject"]
        request(base, "DELETE", f"/api/tickets/{saved['id']}", expected=204)
        args.verify_state.unlink()
        print("PASS: ticket survived service restart; synthetic ticket removed")
        return
    subject = "Smoke " + uuid4().hex
    ticket = request(
        base,
        "POST",
        "/api/tickets",
        {
            "subject": subject,
            "requester_email": "smoke@example.com",
            "priority": "URGENT",
        },
        201,
    )
    path = f"/api/tickets/{ticket['id']}"
    keep = False
    try:
        assert request(base, "GET", path)["subject"] == subject
        matching = request(
            base, "GET", "/api/tickets?search=" + subject.replace(" ", "%20")
        )
        assert any(row["id"] == ticket["id"] for row in matching)
        updated = request(
            base, "PUT", path, {"status": "IN_PROGRESS", "assignee": "Smoke test"}
        )
        assert updated["status"] == "IN_PROGRESS"
        stats = request(base, "GET", "/api/tickets/stats")
        assert stats["total"] >= 1 and stats["inProgress"] >= 1 and stats["urgent"] >= 1
        assert (
            request(base, "PATCH", path, {"status": "RESOLVED"})["status"] == "RESOLVED"
        )
        request(
            base,
            "POST",
            "/api/tickets",
            {"subject": "", "requester_email": "invalid"},
            422,
        )
        with urlopen(base.rstrip("/") + "/metrics", timeout=15) as response:
            assert b"http_requests_total" in response.read()
        if args.persist_state:
            args.persist_state.write_text(
                json.dumps({"id": ticket["id"], "subject": subject}) + "\n"
            )
            keep = True
            print(
                "PASS: HTTP CRUD, filters, validation, statistics and metrics; synthetic ticket retained for restart verification"
            )
        else:
            print("PASS: HTTP CRUD, filters, validation, statistics and metrics")
    finally:
        if not keep:
            request(base, "DELETE", path, expected=204)
            request(base, "GET", path, expected=404)


if __name__ == "__main__":
    main()

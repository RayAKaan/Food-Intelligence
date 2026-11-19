import io
import json

import pytest

from food_intelligence.research_api import RequestError, application, build_research_brief
from food_intelligence.workspace_store import WorkspaceStore


def test_builds_deterministic_draft_from_user_inputs():
    data = {
        "prompt": "Invent a less-sweet chocolate dessert.",
        "ingredients": [{"name": "Dark chocolate", "amount": "180 g"}, {"name": "Dates", "amount": "90 g"}],
        "direction": {"experience": "Creamy centre, delicate crunch"},
    }
    first = build_research_brief(data)
    assert first == build_research_brief(data)
    assert first["status"] == "DRAFT_ONLY"
    assert first["scientific_execution"] == "NOT_RUN"
    assert first["brief_id"].startswith("research_brief_")
    assert len(first["research_questions"]) == 5


@pytest.mark.parametrize("data", [
    {"prompt": "", "ingredients": []},
    {"ingredients": "chocolate"},
    {"ingredients": [{"name": "   "}]},
    {"ingredients": [{"name": "Chocolate"}, {"name": "chocolate"}]},
    {"ingredients": [{"name": "Chocolate", "amount": 180}]},
    {"ingredients": [{"name": "Chocolate"}], "direction": {"temperature": "90 C"}},
    {"ingredients": [{"name": "Chocolate"}], "direction": {"time": 123}},
    {"ingredients": [{"name": "x"}] * 41},
    {"prompt": "x" * 4001, "ingredients": []},
])
def test_rejects_invalid_brief_inputs(data):
    with pytest.raises(RequestError):
        build_research_brief(data)


def call_wsgi(path, method="GET", payload=None, content_type="application/json", store=None):
    raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
    environ = {
        "REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
    }
    if store is not None:
        environ["food_intelligence.workspace_store"] = store
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)
    body = b"".join(application(environ, start_response))
    return captured, json.loads(body) if body else None


def test_health_endpoint_discloses_capabilities(tmp_path):
    response, data = call_wsgi("/api/health", store=WorkspaceStore(tmp_path / "db.sqlite3"))
    assert response["status"] == "200 OK"
    assert data["scientific_simulation"] is False
    assert "project_persistence" in data["capabilities"]


def test_project_and_brief_api_round_trip(tmp_path):
    store = WorkspaceStore(tmp_path / "db.sqlite3")
    response, created = call_wsgi("/api/projects", "POST", {"name": "Chocolate study"}, store=store)
    assert response["status"] == "201 Created"
    project_id = created["project"]["project_id"]
    response, listed = call_wsgi("/api/projects", store=store)
    assert response["status"] == "200 OK"
    assert listed["projects"][0]["name"] == "Chocolate study"
    payload = {"prompt": "Make a new dessert", "ingredients": [{"name": "Cocoa"}]}
    response, brief = call_wsgi(f"/api/projects/{project_id}/briefs", "POST", payload, store=store)
    assert response["status"] == "201 Created"
    assert brief["status"] == "DRAFT_ONLY"
    response, saved = call_wsgi(f"/api/projects/{project_id}/briefs", store=store)
    assert response["status"] == "200 OK"
    assert saved["briefs"] == [brief]


def test_unknown_project_returns_404(tmp_path):
    response, body = call_wsgi("/api/projects/missing", store=WorkspaceStore(tmp_path / "db.sqlite3"))
    assert response["status"] == "404 Not Found"
    assert body["error"] == "not_found"


def test_invalid_project_payload_returns_400(tmp_path):
    response, body = call_wsgi("/api/projects", "POST", {"name": " "}, store=WorkspaceStore(tmp_path / "db.sqlite3"))
    assert response["status"] == "400 Bad Request"
    assert body["error"] == "invalid_request"


def test_legacy_research_brief_endpoint_still_works(tmp_path):
    response, body = call_wsgi(
        "/api/research-brief", "POST",
        {"prompt": "Make a new dessert", "ingredients": [{"name": "Cocoa"}]},
        store=WorkspaceStore(tmp_path / "db.sqlite3"),
    )
    assert response["status"] == "201 Created"
    assert body["status"] == "DRAFT_ONLY"


def test_static_frontend_is_served_by_same_origin_api(tmp_path):
    response, body = call_wsgi("/", store=WorkspaceStore(tmp_path / "db.sqlite3"))
    assert response["status"] == "200 OK"

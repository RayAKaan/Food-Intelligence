import io
import json

import pytest

from food_intelligence.research_api import (
    RequestError,
    application,
    build_research_brief,
)


def test_builds_deterministic_draft_from_user_inputs():
    data = {
        "prompt": "Invent a less-sweet chocolate dessert.",
        "ingredients": [
            {"name": "Dark chocolate", "amount": "180 g"},
            {"name": "Dates", "amount": "90 g"},
        ],
        "direction": {"experience": "Creamy centre, delicate crunch"},
    }
    first = build_research_brief(data)
    second = build_research_brief(data)
    assert first == second
    assert first["status"] == "DRAFT_ONLY"
    assert first["scientific_execution"] == "NOT_RUN"
    assert first["brief_id"].startswith("research_brief_")
    assert len(first["research_questions"]) == 5
    assert first["ingredients"][0]["amount"] == "180 g"


def test_unknown_and_unmeasured_properties_are_not_invented():
    result = build_research_brief({
        "ingredients": [{"name": "Cardamom"}],
        "direction": {},
    })
    assert result["ingredients"] == [{"name": "Cardamom", "amount": None}]
    assert "nutrition" not in result
    assert "predictions" not in result
    assert result["scientific_execution"] == "NOT_RUN"


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


def call_wsgi(path, method="GET", payload=None, content_type="application/json"):
    raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(raw)),
        "wsgi.input": io.BytesIO(raw),
    }
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(application(environ, start_response))
    return captured, body


def test_health_endpoint_discloses_current_capabilities():
    response, body = call_wsgi("/api/health")
    assert response["status"] == "200 OK"
    data = json.loads(body)
    assert data["status"] == "ok"
    assert data["scientific_simulation"] is False


def test_post_endpoint_returns_structured_draft():
    response, body = call_wsgi(
        "/api/research-brief",
        method="POST",
        payload={"prompt": "Make a new dessert", "ingredients": [{"name": "Cocoa"}]},
    )
    assert response["status"] == "201 Created"
    data = json.loads(body)
    assert data["status"] == "DRAFT_ONLY"
    assert data["ingredients"][0]["name"] == "Cocoa"


def test_post_endpoint_returns_client_error_for_invalid_json_shape():
    response, body = call_wsgi("/api/research-brief", method="POST", payload=[])
    assert response["status"] == "400 Bad Request"
    assert json.loads(body)["error"] == "invalid_research_brief"


def test_post_endpoint_requires_json_content_type():
    response, _ = call_wsgi(
        "/api/research-brief",
        method="POST",
        payload={"ingredients": [{"name": "Cocoa"}]},
        content_type="text/plain",
    )
    assert response["status"] == "400 Bad Request"


def test_static_frontend_is_served_by_same_origin_api():
    response, body = call_wsgi("/")
    assert response["status"] == "200 OK"
    assert b"Research Kitchen" in body


def test_unknown_api_route_is_not_served_as_a_static_file():
    response, body = call_wsgi("/api/missing")
    assert response["status"] == "404 Not Found"
    assert json.loads(body)["error"] == "not_found"

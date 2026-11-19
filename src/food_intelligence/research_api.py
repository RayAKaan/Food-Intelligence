"""Small dependency-free HTTP API for the Digital Kitchen prototype.

This service captures and structures research briefs. It does not invoke an
LLM, infer food chemistry, or execute a scientific simulation.
"""
from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any
from wsgiref.simple_server import make_server

from .world_contracts import canonical_json, stable_id

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
MAX_BODY_BYTES = 32_768
MAX_INGREDIENTS = 40


class RequestError(ValueError):
    """A client request is malformed or outside the supported contract."""


def _json_response(start_response: Any, status: str, payload: dict[str, Any]) -> list[bytes]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    start_response(status, [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
    ])
    return [body]


def _read_brief(environ: dict[str, Any]) -> dict[str, Any]:
    if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
        raise RequestError("Content-Type must be application/json")
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError as exc:
        raise RequestError("Content-Length must be an integer") from exc
    if length < 1:
        raise RequestError("Request body is required")
    if length > MAX_BODY_BYTES:
        raise RequestError("Request body exceeds 32 KB")
    raw = environ["wsgi.input"].read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RequestError("Request body must be valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise RequestError("Request body must be a JSON object")
    return data


def build_research_brief(data: dict[str, Any]) -> dict[str, Any]:
    """Validate user-provided inputs and return an explicitly unverified draft."""
    prompt = data.get("prompt", "")
    if not isinstance(prompt, str) or len(prompt) > 4_000:
        raise RequestError("prompt must be text no longer than 4,000 characters")
    ingredients = data.get("ingredients", [])
    if not isinstance(ingredients, list) or len(ingredients) > MAX_INGREDIENTS:
        raise RequestError("ingredients must be a list of at most 40 items")

    normalized: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for item in ingredients:
        if not isinstance(item, dict):
            raise RequestError("each ingredient must be an object")
        name = item.get("name")
        amount = item.get("amount")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            raise RequestError("each ingredient needs a name of 1–100 characters")
        if amount is not None and (not isinstance(amount, str) or len(amount) > 40):
            raise RequestError("ingredient amount must be text of at most 40 characters")
        key = name.strip().casefold()
        if key in seen:
            raise RequestError(f"duplicate ingredient: {name.strip()}")
        seen.add(key)
        normalized.append({"name": name.strip(), "amount": amount.strip() if amount else None})

    direction = data.get("direction", {})
    if not isinstance(direction, dict):
        raise RequestError("direction must be an object")
    allowed_direction = {"experience", "flavour", "time"}
    if set(direction) - allowed_direction:
        raise RequestError("direction contains unsupported fields")
    clean_direction: dict[str, str] = {}
    for key, value in direction.items():
        if not isinstance(value, str) or len(value) > 300:
            raise RequestError(f"direction.{key} must be text of at most 300 characters")
        clean_direction[key] = value.strip()

    if not prompt.strip() and not normalized:
        raise RequestError("provide a research prompt or at least one ingredient")

    questions = [
        "Which desired outcomes can be translated into measurable variables?",
        "Which ingredient properties need traceable source data before modelling?",
        "What process conditions and equipment must be specified?",
        "Which controlled variations would distinguish the candidate formulations?",
        "What physical measurements and sensory evaluations would validate the result?",
    ]
    payload = {
        "prompt": prompt.strip(),
        "ingredients": normalized,
        "direction": clean_direction,
    }
    brief_id = stable_id("research_brief", payload)
    title_source = prompt.strip() or "New ingredient formulation"
    return {
        "brief_id": brief_id,
        "title": title_source[:80],
        "status": "DRAFT_ONLY",
        "scientific_execution": "NOT_RUN",
        "ingredients": normalized,
        "direction": clean_direction,
        "prompt": prompt.strip(),
        "research_questions": questions,
        "limitations": [
            "This endpoint only structures user-provided information.",
            "No literature retrieval, LLM reasoning, food-science solver, or experiment was executed.",
            "No recipe feasibility, taste, texture, nutrition, or safety outcome has been validated.",
        ],
        "canonical_payload": canonical_json(payload),
    }


def application(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    if path == "/api/health" and method == "GET":
        return _json_response(start_response, "200 OK", {
            "status": "ok",
            "service": "food-intelligence-research-brief-api",
            "capabilities": ["brief_validation", "brief_structuring"],
            "scientific_simulation": False,
        })

    if path == "/api/research-brief":
        if method != "POST":
            return _json_response(start_response, "405 Method Not Allowed", {
                "error": "method_not_allowed",
                "message": "Use POST for research brief creation.",
            })
        try:
            brief = build_research_brief(_read_brief(environ))
        except RequestError as exc:
            return _json_response(start_response, "400 Bad Request", {
                "error": "invalid_research_brief",
                "message": str(exc),
            })
        return _json_response(start_response, "201 Created", brief)

    if path.startswith("/api/"):
        return _json_response(start_response, "404 Not Found", {
            "error": "not_found",
            "message": "Unknown API endpoint.",
        })

    if method not in {"GET", "HEAD"}:
        return _json_response(start_response, "405 Method Not Allowed", {
            "error": "method_not_allowed",
        })

    relative = "index.html" if path == "/" else path.lstrip("/")
    target = (APP_ROOT / relative).resolve()
    if APP_ROOT.resolve() not in target.parents and target != APP_ROOT.resolve():
        return _json_response(start_response, "404 Not Found", {"error": "not_found"})
    if not target.is_file():
        return _json_response(start_response, "404 Not Found", {"error": "not_found"})
    content = target.read_bytes()
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    start_response("200 OK", [
        ("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith(("text/", "application/javascript")) else content_type),
        ("Content-Length", str(len(content))),
        ("X-Content-Type-Options", "nosniff"),
    ])
    return [b"" if method == "HEAD" else content]


def main() -> None:
    with make_server("127.0.0.1", 4173, application) as server:
        print("Food Intelligence Digital Kitchen: http://127.0.0.1:4173")
        print("Research brief API: http://127.0.0.1:4173/api/health")
        server.serve_forever()


if __name__ == "__main__":
    main()

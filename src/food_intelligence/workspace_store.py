"""SQLite-backed persistence for Digital Kitchen projects and research briefs."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1


class WorkspaceNotFound(LookupError):
    """A requested workspace resource does not exist."""


class WorkspaceStore:
    def __init__(self, database_path: str | Path | None = None) -> None:
        configured = database_path or os.environ.get("FOOD_INTELLIGENCE_DB")
        self.database_path = Path(configured) if configured else Path.home() / ".food-intelligence" / "workspace.sqlite3"
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute("CREATE TABLE IF NOT EXISTS workspace_schema (version INTEGER NOT NULL)")
            row = db.execute("SELECT version FROM workspace_schema LIMIT 1").fetchone()
            if row is None:
                db.execute("INSERT INTO workspace_schema(version) VALUES (?)", (SCHEMA_VERSION,))
            elif row["version"] > SCHEMA_VERSION:
                raise RuntimeError("Workspace database schema is newer than this application.")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 120),
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS research_briefs (
                    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
                    brief_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status = 'DRAFT_ONLY'),
                    scientific_execution TEXT NOT NULL CHECK(scientific_execution = 'NOT_RUN'),
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(project_id, brief_id)
                );
                CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC, project_id ASC);
                CREATE INDEX IF NOT EXISTS idx_briefs_project ON research_briefs(project_id, created_at ASC, brief_id ASC);
            """)

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def create_project(self, name: str, description: str = "") -> dict[str, Any]:
        clean_name, clean_description = name.strip(), description.strip()
        if not clean_name or len(clean_name) > 120:
            raise ValueError("Project name must be 1–120 characters.")
        if len(clean_description) > 2_000:
            raise ValueError("Project description must be at most 2,000 characters.")
        now, project_id = self._now(), "project_" + uuid.uuid4().hex
        with self._connection() as db:
            db.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
                       (project_id, clean_name, clean_description, now, now))
        return self.get_project(project_id)

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connection() as db:
            rows = db.execute("""
                SELECT p.*, COUNT(b.brief_id) AS brief_count
                FROM projects p LEFT JOIN research_briefs b USING(project_id)
                GROUP BY p.project_id
                ORDER BY p.updated_at DESC, p.project_id ASC
            """).fetchall()
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._connection() as db:
            row = db.execute("""
                SELECT p.*, COUNT(b.brief_id) AS brief_count
                FROM projects p LEFT JOIN research_briefs b USING(project_id)
                WHERE p.project_id = ? GROUP BY p.project_id
            """, (project_id,)).fetchone()
        if row is None:
            raise WorkspaceNotFound("Project not found.")
        return dict(row)

    def save_brief(self, project_id: str, brief: dict[str, Any]) -> dict[str, Any]:
        if brief.get("status") != "DRAFT_ONLY" or brief.get("scientific_execution") != "NOT_RUN":
            raise ValueError("Only unexecuted research drafts can be stored by this endpoint.")
        brief_id = brief.get("brief_id")
        if not isinstance(brief_id, str) or not brief_id:
            raise ValueError("Brief is missing its identifier.")
        payload = json.dumps(brief, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        now = self._now()
        with self._connection() as db:
            if db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                raise WorkspaceNotFound("Project not found.")
            existing = db.execute(
                "SELECT payload_json FROM research_briefs WHERE project_id = ? AND brief_id = ?",
                (project_id, brief_id),
            ).fetchone()
            if existing is not None:
                if existing["payload_json"] != payload:
                    raise ValueError("Brief identifier already exists with different content.")
                return json.loads(existing["payload_json"])
            db.execute("""
                INSERT INTO research_briefs
                (project_id, brief_id, title, status, scientific_execution, payload_json, created_at)
                VALUES (?, ?, ?, 'DRAFT_ONLY', 'NOT_RUN', ?, ?)
            """, (project_id, brief_id, str(brief.get("title", "Research brief"))[:120], payload, now))
            db.execute("UPDATE projects SET updated_at = ? WHERE project_id = ?", (now, project_id))
        return json.loads(payload)

    def list_briefs(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            if db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                raise WorkspaceNotFound("Project not found.")
            rows = db.execute("""
                SELECT payload_json FROM research_briefs
                WHERE project_id = ? ORDER BY created_at ASC, brief_id ASC
            """, (project_id,)).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

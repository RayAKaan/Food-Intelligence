import json

import pytest

from food_intelligence.workspace_store import WorkspaceNotFound, WorkspaceStore


def test_project_crud_and_brief_persistence_survive_reopen(tmp_path):
    path = tmp_path / "workspace.sqlite3"
    store = WorkspaceStore(path)
    project = store.create_project("Chocolate study", "Test formulations")
    brief = {
        "brief_id": "research_brief_example", "title": "Chocolate",
        "status": "DRAFT_ONLY", "scientific_execution": "NOT_RUN",
        "ingredients": [{"name": "Cocoa", "amount": "20 g"}],
    }
    assert store.save_brief(project["project_id"], brief) == brief
    reopened = WorkspaceStore(path)
    assert reopened.get_project(project["project_id"])["brief_count"] == 1
    assert reopened.list_briefs(project["project_id"]) == [brief]
    assert reopened.list_projects()[0]["name"] == "Chocolate study"


def test_project_names_are_validated(tmp_path):
    store = WorkspaceStore(tmp_path / "db.sqlite3")
    with pytest.raises(ValueError):
        store.create_project("   ")
    with pytest.raises(ValueError):
        store.create_project("x" * 121)


def test_missing_project_fails_closed(tmp_path):
    store = WorkspaceStore(tmp_path / "db.sqlite3")
    with pytest.raises(WorkspaceNotFound):
        store.get_project("missing")
    with pytest.raises(WorkspaceNotFound):
        store.list_briefs("missing")


def test_only_unexecuted_drafts_can_be_saved(tmp_path):
    store = WorkspaceStore(tmp_path / "db.sqlite3")
    project = store.create_project("Test")
    with pytest.raises(ValueError):
        store.save_brief(project["project_id"], {
            "brief_id": "x", "status": "EXECUTED", "scientific_execution": "COMPLETE"
        })


def test_duplicate_save_is_idempotent_but_conflicting_content_is_rejected(tmp_path):
    store = WorkspaceStore(tmp_path / "db.sqlite3")
    project = store.create_project("Test")
    brief = {"brief_id": "b1", "status": "DRAFT_ONLY", "scientific_execution": "NOT_RUN"}
    store.save_brief(project["project_id"], brief)
    assert store.save_brief(project["project_id"], brief) == brief
    with pytest.raises(ValueError):
        store.save_brief(project["project_id"], {**brief, "title": "different"})


def test_projects_have_deterministic_ordering_for_equal_timestamps(tmp_path):
    store = WorkspaceStore(tmp_path / "db.sqlite3")
    first = store.create_project("First")
    second = store.create_project("Second")
    with store._connect() as db:
        db.execute("UPDATE projects SET updated_at = 'same' ")
    ids = [item["project_id"] for item in store.list_projects()]
    assert ids == sorted([first["project_id"], second["project_id"]])

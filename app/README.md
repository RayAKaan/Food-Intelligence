# Food Intelligence — Digital Kitchen Workspace

## Run locally

```bash
pip install -e .
python -m food_intelligence.research_api
```

Open `http://127.0.0.1:4173`. Set `FOOD_INTELLIGENCE_DB` to choose a database location. The default is `~/.food-intelligence/workspace.sqlite3`.

## Persistence API

- `GET /api/projects`: list projects and brief counts.
- `POST /api/projects`: create a project with `name` and optional `description`.
- `GET /api/projects/{project_id}`: load project metadata.
- `GET /api/projects/{project_id}/briefs`: list saved research drafts.
- `POST /api/projects/{project_id}/briefs`: validate and save a research draft.
- `GET /api/health`: current service capabilities.

SQLite schema versioning starts at version 1. Projects and briefs use foreign-key integrity; deleting a project cascades to its briefs. Brief saves are idempotent for identical content and reject conflicting content under the same ID.

## Scientific boundary

Saved briefs are still `DRAFT_ONLY` and `NOT_RUN`. Persistence does not imply literature retrieval, LLM reasoning, food-science simulation, experiment execution, or validation of recipe feasibility, taste, texture, nutrition, or safety. No predictions are fabricated.

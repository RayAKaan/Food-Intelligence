# Food Intelligence — Digital Kitchen Workspace

This directory contains the first user-facing workspace and its dependency-free local API.

## Run locally

From the repository root:

```bash
pip install -e .
python -m food_intelligence.research_api
```

Open `http://127.0.0.1:4173`. The same-origin server serves the interface and the research brief API. After installation, the equivalent command is `food-api`.

## What works

- Responsive three-region culinary research workspace.
- Ingredient bench with add/remove interactions.
- Natural-language research brief capture connected to the Python API.
- API validation and deterministic draft brief creation.
- Structured research questions and explicit limitations.
- No frontend build step or JavaScript framework required.

## API

- `GET /api/health`: service and capability status.
- `POST /api/research-brief`: validates and structures a user-provided research brief.

Example request:

```json
{
  "prompt": "Create a less-sweet chocolate dessert with a creamy centre.",
  "ingredients": [
    {"name": "Dark chocolate", "amount": "180 g"},
    {"name": "Dates", "amount": "90 g"}
  ],
  "direction": {
    "experience": "Creamy centre, delicate crunch",
    "flavour": "Deep cacao, warm spice",
    "time": "Under 30 minutes"
  }
}
```

The response is deterministic and marked `DRAFT_ONLY` / `NOT_RUN`. It contains the submitted ingredients, direction, research questions, and limitations.

## Scientific boundary

This API only validates and structures user input. It does not call an LLM, retrieve literature, infer ingredient chemistry, run a food-science solver, persist projects, or validate recipe outcomes. It never fabricates predictions, nutrition values, or safety assessments.

## Next integration steps

1. Add persistent project and experiment storage.
2. Add source-backed ingredient data and evidence retrieval.
3. Define a provider interface for optional LLM-assisted research planning.
4. Add validated scientific solvers only with sourced assumptions and tests.

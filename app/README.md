# Food Intelligence — Digital Kitchen Workspace

This directory contains the first visual product prototype for Food Intelligence.

## Run locally

Open `index.html` in a browser, or serve this directory with any static file server:

```bash
python -m http.server 4173 --directory app
```

Then visit `http://localhost:4173`.

No frontend build step or third-party JavaScript dependency is required. Google Fonts are optional; the interface falls back to system fonts if they are unavailable.

## What works

- Responsive three-column research workspace.
- Ingredient bench with add/remove interactions.
- Natural-language research brief capture.
- Structured draft brief dialog.
- Navigation affordances and prototype status messages.

## Important boundary

This is a frontend interaction prototype, not a connected AI scientist. It does not call an LLM, run a food-science solver, persist projects, or claim to validate a recipe. The research brief dialog explicitly labels its output as a draft and lists the scientific questions still requiring evidence and experiments.

## Next integration steps

1. Define API contracts between this UI and the Python research core.
2. Add project and ingredient persistence.
3. Connect a research orchestrator behind explicit provider interfaces.
4. Add validated scientific solvers and experiment execution only when their assumptions, parameter sources, and validation tests are documented.

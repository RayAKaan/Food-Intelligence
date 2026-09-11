# ADR-006: research and commercial manifests are separate

## Decision
Every dataset gets an explicit status. Only `COMMERCIAL_SAFE` sources enter the commercial candidate manifest; `LEGAL_REVIEW_REQUIRED` and `RESEARCH_ONLY` sources remain isolated.

## Consequence
The research branch can test molecular/sensory adapters without silently contaminating a future commercial artifact.

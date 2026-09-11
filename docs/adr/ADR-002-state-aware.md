# ADR-002: Ingredient states are first-class

## Context
Raw garlic and fried garlic are not interchangeable evidence units; merging states creates false process and sensory conclusions.

## Decision
Use Ingredient as a base identity and IngredientState as a separate node with parent/state transitions. Raw source text is retained.

## Consequences
More rows and explicit unknowns, but safer entity resolution and a path to transformation experiments.

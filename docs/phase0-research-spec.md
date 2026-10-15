# Phase 0 — Research Specification: Computational Food World

## Mission

Food-Intelligence is being developed as an executable experimental world in which AI agents investigate food systems through controlled interventions, observe outcomes, compare results with predictions, and improve future experiments. It is not merely a recipe recommender, a food knowledge graph, or a language model that answers from its training data.

The graph, canonical data, scientific solvers, predictive models, and agent are components of this world. The defining capability is a reproducible experimental feedback loop.

## Target experimental loop

1. Define a versioned initial world state.
2. Formulate a falsifiable hypothesis.
3. Select an intervention and controlled variables.
4. Execute an experiment through the world dynamics engine.
5. Return typed observations with conditions, provenance, and uncertainty.
6. Compare observations against predictions and baselines.
7. Persist the full experiment record.
8. Select a subsequent experiment based on the result and remaining uncertainty.

A model-generated answer is not an observation. Simulated outputs, physical measurements, and inferences must remain distinguishable.

## Core scientific domains

- Food identity, composition, ingredient states, and culinary context.
- Chemistry: compounds, concentrations, supported reactions, and degradation.
- Physics: heat and mass transfer, physical properties, and state changes.
- Processing: temperature, time, sequence, mixing, fermentation, drying, and other supported interventions.
- Sensory science: taste, odor, aroma release, and texture where data and models support those claims.
- Experimental design, uncertainty, reproducibility, and evidence provenance.

The first implementation should be narrow and testable. A small system involving spices, oils, heating conditions, and selected measurable outcomes is preferable to a broad simulator that cannot be validated.

## Scientific integrity requirements

- Every observation must identify whether it is measured, simulated, or inferred.
- Every admitted data asset must have source, version, checksum where applicable, license/permission status, and permitted-use metadata.
- Missing values must not be silently converted to zero.
- Hypotheses must not be promoted to established facts without suitable evidence.
- Synthetic data may support software regression tests but cannot establish real-world scientific validity.
- Every model must document its assumptions, operating range, and evaluation method.
- Experimental failures and negative results must be retained.
- Results must be reproducible from versioned conditions, code, models, and inputs where technically possible.
- No access controls or dataset licenses may be bypassed.

## Hardware and dependency constraints

The research path must remain useful on a GTX 1650, Ryzen 3 3100, and 16 GB RAM. Prioritize deterministic scientific code, efficient tabular processing, classical machine learning, compact predictive models, and small open-weight models. Large-model training is not a prerequisite for the first experimental loop.

Use established open-source scientific components when their capabilities and licenses fit. Review software, model-weight, and dataset licenses separately.

## Architectural boundaries

- **World state:** canonical representation of the simulated food system.
- **Intervention API:** validated changes to the world state.
- **Dynamics engine:** deterministic solvers and bounded predictive models.
- **Experiment runner:** reproducible execution and controlled comparisons.
- **Observation system:** typed outputs, provenance, uncertainty, and failure reporting.
- **Experimental memory:** immutable or versioned records of hypotheses, conditions, predictions, and outcomes.
- **AI scientist:** proposes hypotheses, selects experiments, and interprets returned results.
- **Learning loop:** evaluates prediction errors and updates eligible models or beliefs.
- **Validation system:** compares predictions against held-out data and physical measurements.

The knowledge graph is a derived, queryable representation of entities and relationships; it is not a substitute for executable dynamics.

## Success criteria

The initial end-to-end milestone is achieved only when an agent can execute a bounded experiment, receive a reproducible result, compare it with a prior prediction, save the evidence, and choose a subsequent experiment. Improvement must be measured on held-out experiments against a documented baseline.

Physical validity can only be claimed for domains compared against suitable real measurements. A successful simulator test alone is not physical validation.

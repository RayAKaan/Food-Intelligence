from .core import Evidence, Ingredient, Resolver, cosine, complementarity, compatibility, novelty

from .representation_builder import build_explicit_representation, semantic_representation, molecular_representation
from .transformations import ProcessSpec, TransformationRecord, validate_transformation, instantiate, transition_template

from .intelligence import Candidate, CandidateRequest, FoodIntelligenceEngine
from .graph import GraphNode, GraphEdge, FoodKnowledgeGraph
from .query import FoodQuery, QueryPlan, QueryPlanner, FoodRetriever
from .fusion import MultiViewFusion, FusionResult
from .novelty import NoveltyEngine, NoveltySignals

from .retrieval import MultiViewIndex
from .constraints import ConstraintEngine, ConstraintSet, ConstraintResult
from .compatibility_v2 import CompatibilityV2, CompatibilityConfig
from .reasoning import FoodReasoner, ReasoningConfig
from .pareto import pareto_frontier
from .pipeline import FoodIntelligencePipeline, PipelineConfig, PipelineResult
from .evaluation import bootstrap_ci, paired_bootstrap_delta, run_ablation, failure_analysis, real_corpus_readiness, research_readiness_gate, run_full_evaluation
from .benchmark_tasks import AliasCase, run_alias_benchmark, run_state_resolution_benchmark, run_constraint_benchmark, run_process_validity_benchmark, run_heldout_pair_benchmark, run_all_tasks

from .ingest_pipeline import ManifestRecord, verify_checksum, detect_schema, run_ingestion, status_without_snapshot, INGESTION_PIPELINE_VERSION

__version__ = "0.1.0"
# Canonical contracts for the executable experimental world.
from .world_contracts import (
    CONTRACTS_VERSION,
    EvidenceClass,
    EvidenceRecord,
    ExperimentProtocol,
    ExperimentRecord,
    ExperimentStatus,
    ExperimentalObservation,
    Hypothesis,
    Intervention,
    ObservationStatus,
    Prediction,
    Quantity,
    UncertaintyEstimate,
    WorldComponent,
    WorldState,
    canonical_json,
    stable_id,
)

# Explicit adapters for reconciling legacy records with canonical contracts.
from .contract_adapters import (
    canonical_process_id,
    canonical_state_id,
    legacy_observation_to_contract,
    legacy_provenance_to_evidence,
    legacy_sensory_profile_to_observations,
    preserve_entity_id,
)

# Dimensional units and measurement metadata for experimental values.
from .units import (
    UnitDefinition,
    UNIT_REGISTRY,
    assert_compatible_units,
    convert_quantity,
    convert_value,
    normalize_quantity,
    unit_definition,
    unit_dimension,
)
from .measurement import MeasurementMetadata, convert_observation_unit

# Provenance-aware evidence ledger; contradictions remain explicit and unresolved.
from .evidence_ledger import (
    EvidenceAudit,
    EvidenceIssue,
    EvidenceLedger,
    EvidenceLink,
    EvidenceRelation,
)

# Cross-contract integrity checks and explicit schema migration policy.
from .cross_contracts import (
    ContractIssue,
    ContractValidationReport,
    IssueSeverity,
    SchemaMigrationRegistry,
    validate_experiment_bundle,
)

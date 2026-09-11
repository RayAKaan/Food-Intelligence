# Risk register

| ID | Risk | Severity | Trigger | Mitigation/owner |
|---|---|---|---|---|
| R1 | incompatible data license | critical | source status not explicit | quarantine and legal review |
| R2 | false novelty | critical | small/incomplete index | corpus-relative labels |
| R3 | unsafe suggestion | critical | ingredient safety unknown | hard safety gate; no positive safety claims |
| R4 | state collapse | critical | raw/prepared alias collision | state IDs and review queue |
| R5 | recipe leakage | high | near duplicates cross split | family/source deduplication |
| R6 | sparse sensory data | high | missing modality/context | null + confidence, no imputation to zero |
| R7 | chemistry false positive | high | pairing inferred from compounds | typed evidence and independent validation |
| R8 | LLM unsupported claim | high | generated source assertion | claim validator/evidence ledger |

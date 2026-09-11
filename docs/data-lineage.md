# Data lineage

Required chain:

```text
raw snapshot
  -> parsed source record
  -> normalized recipe / ingredient text
  -> canonical recipe group and ingredient identity
  -> ingredient-state and process entities
  -> frequency and pairing evidence
  -> model feature
```

Every edge must retain dataset, source ID, source record ID, license status, retrieval date, checksum, parser version, normalization version, and ontology version. Research and commercial lineage are separate graphs; no commercial entity may point to a research-only source.
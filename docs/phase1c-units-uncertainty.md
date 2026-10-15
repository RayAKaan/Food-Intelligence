# Phase 1C — Units, Values, and Uncertainty

## Scope

Phase 1C adds strict, dependency-free dimensional conversion and explicit measurement metadata. It does not change the generic \`Quantity\` constructor to require a registry-known unit: existing records may use domain-specific units such as \`score\` or \`relative\`. Such units can be represented, but conversion fails closed unless the unit is registered.

## Implemented

- A unit registry for mass, volume, length, time, temperature, pressure, energy, power, amount of substance, concentration, mass fraction, dimensionless values, pH, sensory scores, and relative measurements.
- Dimensional compatibility checks: for example, mass cannot be converted to volume, and mass/volume cannot be silently treated as mass/mass.
- Scalar conversion with affine temperature offsets.
- Quantity conversion that preserves unknown values and transforms uncertainty bounds and standard deviations correctly.
- Canonical normalization into each registered dimension's base unit.
- Measurement metadata for method, replicate count, instrument, calibration state, detection and quantification limits, sample matrix, sampling method, timestamp, uncertainty, and notes.
- Detection-limit validation including unit compatibility and the rule that a known quantification limit cannot be below a known detection limit.
- Safe conversion of numeric experimental observations while preserving observation identity, evidence class, source record, conditions, and uncertainty.
- Tests for conversion correctness, incompatible dimensions, missing values, uncertainty, measurement metadata, and observation conversion.

## Unit semantics

Conversions use registered definitions of the form:

\`base_value = value * scale + offset\`

Only units with the same declared dimension are convertible. Standard deviation scales by the absolute scale ratio and is not translated by affine offsets; interval bounds are converted as values. Unknown values remain unknown. No implicit unit inference is performed.

The registry uses explicit symbols, including \`degC\`, \`degF\`, \`K\`, \`ug\`, and \`uL\`. It accepts common Unicode aliases for micro-units and Celsius/Fahrenheit. The API intentionally rejects unregistered spellings rather than guessing.

## Scientific boundary

- Unit conversion is arithmetic, not scientific validation.
- The existence of a measurement record does not guarantee instrument calibration or experimental quality.
- A measurement's uncertainty is retained as reported; this phase does not estimate uncertainty from raw data.
- pH is treated as its own registered scale and is not converted to concentration.
- Sensory scores and relative units are not interchangeable with physical dimensions.
- This unit registry is a controlled starting set; expansion requires tests and explicit dimension definitions.

## Exit checks

- CI passes the full test suite and CLI smoke tests on Python 3.10–3.13.
- Compatible units convert deterministically; incompatible or unknown units fail closed.
- Unknown values remain missing through conversion.
- Measurement metadata validates replicate count, calibration status, timestamp syntax, and limit ordering.
- Numeric observation conversion preserves provenance/evidence metadata and uncertainty.

# Recipe-evidence pairing baseline

The first baseline is recipe co-occurrence only. For an admitted corpus it emits pair count, recipe count, smoothed NPMI, source-record evidence, and `SOURCE_DERIVED`. It does not claim chemical or sensory compatibility. Minimum pair-count controls are required; the default implementation uses a minimum of one for inspection, while scientific reports should set a higher threshold when corpus size permits.

Current result: not run on the research corpus because it has zero admitted recipe records. It is not scientifically meaningful on the single Sangat nutrition record.
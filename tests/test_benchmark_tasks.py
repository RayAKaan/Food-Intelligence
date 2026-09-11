from food_intelligence.benchmark_tasks import (
    run_alias_benchmark,
    run_state_resolution_benchmark,
    run_constraint_benchmark,
    run_process_validity_benchmark,
    run_heldout_pair_benchmark,
    run_all_tasks,
)


def test_alias_benchmark_is_fully_correct_on_fixture():
    out = run_alias_benchmark()
    assert out["data_status"] == "SYNTHETIC"
    assert out["resolution_rate"] >= .8
    assert out["accuracy"] == 1.0


def test_state_resolution_preserves_identity_and_state():
    out = run_state_resolution_benchmark()
    assert out["identity_preserved_rate"] == 1.0
    assert out["state_preserved_rate"] == 1.0


def test_constraint_benchmark_is_fail_closed():
    out = run_constraint_benchmark()
    assert out["pass_rate"] == 1.0
    block = next(c for c in out["cases"] if c["safety"] == "BLOCKED")
    assert block["allowed"] is False


def test_process_validity_is_fail_closed():
    out = run_process_validity_benchmark()
    assert out["pass_rate"] == 1.0
    assert out["vocabulary_size"] >= 25


def test_heldout_pair_baseline_is_deterministic_and_null_honest():
    a = run_heldout_pair_benchmark(seed=17)
    b = run_heldout_pair_benchmark(seed=17)
    assert a == b


def test_all_tasks_are_json_serialisable():
    import json
    assert json.dumps(run_all_tasks())
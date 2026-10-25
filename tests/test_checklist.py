from pathlib import Path

import checklist as cl
from conftest import FIXTURES

ITEMS = cl.load()["items"]
BASELINE = FIXTURES / "runs" / "baseline__1"
GOOD = FIXTURES / "runs" / "with-setup__1"


def item(iid):
    return next(i for i in ITEMS if i["id"] == iid)


def test_starting_checklist_is_valid():
    assert cl.validate(cl.load()) == []


def test_validate_rejects_bad_regex_duplicate_ids_and_unknown_structural():
    data = {"items": [
        {"id": "a", "title": "t", "review": "r", "explore": "e", "patterns": [{"regex": "("}]},
        {"id": "a", "title": "t", "review": "r", "explore": "e", "structural": "nope"},
        {"id": "Bad Id", "title": "", "review": "r", "explore": "e"},
    ]}
    errors = "\n".join(cl.validate(data))
    assert "bad pattern" in errors and "duplicate id: a" in errors
    assert "unknown structural check" in errors and "bad id" in errors and "title must be" in errors


def test_pattern_counts_per_kloc():
    src = BASELINE / "src" / "counter.js"
    got = cl.count_patterns([src], BASELINE, [item("empty-catch"), item("hardcoded-colors"), item("debug-output-left")], loc=100)
    assert got["empty-catch"]["hits"] == 1
    assert got["hardcoded-colors"] == {"hits": 1, "per_kloc": 10.0, "files": ["src/counter.js"]}
    assert got["debug-output-left"]["hits"] == 1


def test_pattern_counting_skips_very_long_lines(tmp_path):
    f = tmp_path / "min.js"
    f.write_text("console.log(1);" + "x" * cl.MAX_LINE + "\n")
    assert cl.count_patterns([f], tmp_path, [item("debug-output-left")], loc=1)["debug-output-left"]["hits"] == 0


def test_structural_flags_bad_run():
    got = cl.structural(BASELINE, BASELINE, FIXTURES / "SPEC.md")
    assert got["spec_modified"] == {"flagged": True, "modified": True}
    assert got["missing_lockfile"]["flagged"]
    assert got["build_artifacts"]["dirs"] == ["dist"]
    assert got["open_items"]["count"] == 2
    assert got["no_tests"]["flagged"]


def test_structural_passes_clean_run():
    got = cl.structural(GOOD, GOOD, FIXTURES / "SPEC.md")
    assert not any(v["flagged"] for v in got.values())


def test_spec_check_is_not_flagged_without_a_pristine_spec():
    assert cl.structural(BASELINE, BASELINE, None)["spec_modified"] == {"flagged": False, "modified": None}


def test_applicable_filters_by_kind_and_spec():
    items = [{"id": "a", "applies_to": ["node"]}, {"id": "b", "applies_to": ["dart"]},
             {"id": "c", "applies_if_spec_matches": "winery"}]
    assert [i["id"] for i in cl.applicable(items, "node", "a counter")] == ["a"]
    assert [i["id"] for i in cl.applicable(items, "node", "A Winery app")] == ["a", "c"]


def test_calibration_distribution():
    cal = cl.calibrate([item("empty-catch")], [{"empty-catch": 0}, {"empty-catch": 2.0}, {"empty-catch": 4.0}, {}])
    assert cal["empty-catch"] == {"n": 4, "fire_rate": 0.5, "median": 1.0, "p90": 4.0}


def test_prompts_for_reviewer_and_tester_cover_every_item():
    assert [q["id"] for q in cl.review_questions(ITEMS)] == [i["id"] for i in ITEMS]
    assert all(s["step"] for s in cl.explore_steps(ITEMS))

import csv
import json

import analyze as az


def result(run, loc=1000, errors=0, cost=2.0, prompt="p1", fp=None, limit=False, **extra):
    return {
        "run": run, "condition": run.split("__")[0], "kind": "node", "loc": loc, "prompt_hash": prompt,
        "fingerprint": fp or [], "meta": {"cost_usd": cost, "hit_limit": limit},
        "checks": {"analyzer": {"status": "ok", "errors": errors},
                   "typecheck": {"status": "skipped", "reason": "no tsconfig.json"},
                   "hygiene": {}, "mistake_patterns": {"items": {}}},
        "checklist_items": [], "tools": {}, **extra,
    }


def review(run, rating, model="m1"):
    return {"run": run, "model": model, "effort": "high", "overall": {"data": {"rating": rating}, "cost_usd": 0.1}}


def write(tmp_path, results, reviews=()):
    paths = []
    for r in results:
        p = tmp_path / f"{r['run']}.json"
        p.write_text(json.dumps(r))
        paths.append(str(p))
    for rv in reviews:
        p = tmp_path / f"{rv['run']}.review.json"
        p.write_text(json.dumps(rv))
        paths.append(str(p))
    return paths


def build(tmp_path, results, reviews=(), human=None):
    args = type("A", (), {"results": write(tmp_path, results, reviews), "md": str(tmp_path / "r.md"), "human": human})
    az.report(args)
    return (tmp_path / "r.md").read_text()


def test_medians_per_condition_and_per_kloc(tmp_path):
    rs = [result("a__1", loc=1000, errors=10), result("a__2", loc=2000, errors=10), result("a__3", loc=500, errors=0),
          result("b__1", errors=4), result("b__2", errors=8), result("b__3", errors=6)]
    text = build(tmp_path, rs)
    # a: 10/kLOC, 5/kLOC, 0/kLOC -> median 5; b: 4, 8, 6 per kLOC -> median 6
    assert "| Lint errors /kLOC | 5 | 6 |" in text
    assert "| a__1 | 1000 |" in text
    assert "Condition" not in text.split("## Medians")[0]  # three reps each: no rep warning


def test_rating_and_cost_columns_and_rating_per_dollar(tmp_path):
    rs = [result(f"{c}__{i}", cost=cost) for c, cost in (("a", 2.0), ("b", 4.0)) for i in (1, 2, 3)]
    rv = [review(r["run"], 8 if r["condition"] == "a" else 6) for r in rs]
    text = build(tmp_path, rs, rv)
    assert "| Overall rating (1-10) | 8 | 6 |" in text
    assert "| Rating per agent dollar | 4 | 1.5 |" in text


def test_warnings(tmp_path):
    same = [f"line number {i} is long enough to be fingerprinted" for i in range(8)]
    rs = [result("a__1", fp=same, limit=True), result("b__1", prompt="p2", fp=same)]
    text = build(tmp_path, rs, [review("a__1", 10), review("b__1", 9, model="m2")])
    assert "Condition a has 1 rep(s)" in text
    assert "different prompts" in text
    assert "a__1 hit a usage limit" in text
    assert "a__1 and b__1 share 100%" in text
    assert "too easy to separate" in text
    assert "different models" in text


def test_skipped_checks_are_listed(tmp_path):
    text = build(tmp_path, [result("a__1")])
    assert "| a__1 | typecheck | no tsconfig.json |" in text


def test_stubbed_review_gives_no_metrics(tmp_path):
    rv = {**review("a__1", 10), "stub": True}
    text = build(tmp_path, [result("a__1")], [rv])
    assert "Overall rating" not in text and "stubbed" in text


def test_copy_pairs_threshold():
    a = result("a__1", fp=[str(i) for i in range(10)])
    b = result("b__1", fp=[str(i) for i in range(2, 12)])  # 8 of 10 shared
    c = result("c__1", fp=[str(i) for i in range(12, 22)])  # nothing shared
    assert az.copy_pairs([a, b, c]) == [("a__1", "b__1", 0.8)]


def test_spearman():
    assert az.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert az.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert az.spearman([1, 2, 3, 4], [1, 3, 2, 4]) == 0.8
    assert az.spearman([1, 2, 2, 4], [1, 2, 2, 4]) == 1.0  # ties share the average rank
    assert az.spearman([1, 1, 1], [1, 2, 3]) is None  # no variance
    assert az.spearman([1], [1]) is None


def test_sheet_hides_scores_and_condition_order(tmp_path):
    rs = [result(f"{c}__{i}") for c in "ab" for i in (1, 2, 3)]
    out = tmp_path / "human.csv"
    az.sheet(type("A", (), {"results": write(tmp_path, rs, [review("a__1", 7)]), "out": str(out), "seed": "s1"}))
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 6 and all(r["rating_1_to_10"] == "" for r in rows)
    text = out.read_text()
    assert "a__" not in text and "b__" not in text  # no run names, no model score column
    key = json.loads(out.with_suffix(".key.json").read_text())
    assert sorted(key.values()) == sorted(r["run"] for r in rs)
    # the order does not follow the sorted run order and is reproducible with the same seed
    assert [key[r["id"]] for r in rows] != sorted(key.values())
    out2 = tmp_path / "human2.csv"
    az.sheet(type("A", (), {"results": write(tmp_path, rs), "out": str(out2), "seed": "s1"}))
    assert out2.read_text() == text


def test_model_versus_human_correlation_in_report(tmp_path):
    rs = [result(f"a__{i}") for i in range(1, 5)]
    rv = [review(r["run"], m) for r, m in zip(rs, (3, 5, 7, 9))]
    out = tmp_path / "human.csv"
    az.sheet(type("A", (), {"results": write(tmp_path, rs), "out": str(out), "seed": "x"}))
    key = json.loads(out.with_suffix(".key.json").read_text())
    human = {run: score for run, score in zip(sorted(key.values()), (1, 2, 4, 3))}
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "rating_1_to_10", "notes"])
        w.writerows([[i, human[run], ""] for i, run in key.items()])
    text = build(tmp_path, rs, rv, human=str(out))
    assert "Spearman rank correlation over 4 runs: 0.8" in text
    few = build(tmp_path, rs[:3], rv[:3], human=str(out))
    assert "at least 4 are needed" in few


def test_report_ignores_the_sheet_key_picked_up_by_a_glob(tmp_path):
    paths = write(tmp_path, [result("a__1")])
    key = tmp_path / "human.key.json"
    key.write_text('{"Rabc": "a__1"}')
    az.report(type("A", (), {"results": [*paths, str(key)], "md": str(tmp_path / "r.md"), "human": None}))
    assert "| a__1 |" in (tmp_path / "r.md").read_text()

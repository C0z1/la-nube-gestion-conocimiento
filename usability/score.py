"""SUS score + task success from usability/responses.csv -> outputs/usability.json"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sus(answers):
    """Standard SUS: odd items (score-1), even items (5-score), sum x 2.5 -> 0..100."""
    assert len(answers) == 10 and all(1 <= a <= 5 for a in answers), answers
    return 2.5 * sum(a - 1 if i % 2 == 0 else 5 - a for i, a in enumerate(answers))


assert sus([5, 1] * 5) == 100 and sus([1, 5] * 5) == 0 and sus([3] * 10) == 50

if __name__ == "__main__":
    rows = list(csv.DictReader(open(ROOT / "usability" / "responses.csv", encoding="utf-8")))
    rows = [r for r in rows if r["q1"].strip()]
    if not rows:
        raise SystemExit("responses.csv has no answers yet")
    scores = [sus([int(r[f"q{i}"]) for i in range(1, 11)]) for r in rows]
    tasks = {}
    for t in ("t1", "t2", "t3"):
        times = [float(r[t + "_seconds"]) for r in rows if r[t + "_seconds"].strip()]
        tasks[t.upper()] = {"completed": f"{len(times)}/{len(rows)}",
                            "median_seconds": sorted(times)[len(times) // 2] if times else None}
    out = {"testers": len(rows), "SUS_mean": round(sum(scores) / len(scores), 1),
           "SUS_min": min(scores), "SUS_max": max(scores), "tasks": tasks,
           "comments": [r["comment"] for r in rows if r["comment"].strip()]}
    json.dump(out, open(ROOT / "outputs" / "usability.json", "w", encoding="utf-8"), indent=2)
    print(json.dumps(out, indent=2))

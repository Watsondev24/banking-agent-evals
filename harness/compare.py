"""Compare results from two or more eval runs side by side.

Usage:
    python -m harness.compare v1_basic v2_better_tools
    python -m harness.compare v1_basic v2_better_tools v3_xxx
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path("results")


def load_latest(version: str) -> list[dict]:
    """Find the most recent results file for a given version."""
    matches = sorted(RESULTS_DIR.glob(f"{version}_*.json"))
    if not matches:
        raise FileNotFoundError(f"No results found for version: {version}")
    return json.loads(matches[-1].read_text())


def aggregate(results: list[dict]) -> dict:
    """Compute per-version summary metrics."""
    if not results:
        return {}
    n = len(results)
    strict_pass = sum(1 for r in results if r.get("strict_pass"))
    tool_sel = sum(1 for r in results if r.get("tool_selection") == "PASS")
    tool_in = sum(1 for r in results if r.get("tool_input") == "PASS")
    grounded = sum(1 for r in results if r.get("groundedness") == "PASS")
    completion = sum(1 for r in results if r.get("task_completion") == "PASS")
    clarity_vals = [r.get("clarity", 0) for r in results if isinstance(r.get("clarity"), (int, float)) and r.get("clarity")]
    clarity_mean = sum(clarity_vals) / len(clarity_vals) if clarity_vals else 0
    return {
        "n": n,
        "strict_pass_pct": 100 * strict_pass / n,
        "tool_selection_pct": 100 * tool_sel / n,
        "tool_input_pct": 100 * tool_in / n,
        "groundedness_pct": 100 * grounded / n,
        "task_completion_pct": 100 * completion / n,
        "clarity_mean": clarity_mean,
    }


def per_scenario_pass(results: list[dict]) -> dict[str, bool]:
    """Map test_id → pass/fail (one row per scenario)."""
    out = {}
    for r in results:
        out[r["test_id"]] = bool(r.get("strict_pass"))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("versions", nargs="+", help="Versions to compare, e.g. v1_basic v2_better_tools")
    args = parser.parse_args()

    runs = {v: load_latest(v) for v in args.versions}

    # ---- Summary table ----
    print("\n=== SUMMARY (latest run of each version) ===\n")
    header = f"{'Metric':<22}" + "".join(f"{v:>20}" for v in args.versions)
    print(header)
    print("-" * len(header))

    aggregates = {v: aggregate(r) for v, r in runs.items()}
    rows = [
        ("Scenarios run", "n", "{:d}"),
        ("Tool selection %", "tool_selection_pct", "{:.1f}"),
        ("Tool input %", "tool_input_pct", "{:.1f}"),
        ("Groundedness %", "groundedness_pct", "{:.1f}"),
        ("Task completion %", "task_completion_pct", "{:.1f}"),
        ("Clarity (mean)", "clarity_mean", "{:.2f}"),
        ("STRICT PASS RATE %", "strict_pass_pct", "{:.1f}"),
    ]
    for label, key, fmt in rows:
        line = f"{label:<22}"
        for v in args.versions:
            val = aggregates[v].get(key, 0)
            line += f"{fmt.format(val):>20}"
        print(line)

    # ---- Per-scenario diff ----
    print("\n=== PER-SCENARIO PASS/FAIL ===\n")
    per_version = {v: per_scenario_pass(r) for v, r in runs.items()}
    all_ids = sorted({tid for d in per_version.values() for tid in d})

    header = f"{'Scenario':<14}" + "".join(f"{v:>20}" for v in args.versions) + "   Change"
    print(header)
    print("-" * len(header))

    for tid in all_ids:
        marks = []
        for v in args.versions:
            passed = per_version[v].get(tid)
            marks.append("✓" if passed else "✗" if passed is False else "—")
        # Note regressions/improvements between first and last version
        change = ""
        if len(args.versions) >= 2:
            first, last = marks[0], marks[-1]
            if first == "✓" and last == "✗":
                change = "  REGRESSION"
            elif first == "✗" and last == "✓":
                change = "  FIXED"
        line = f"{tid:<14}" + "".join(f"{m:>20}" for m in marks) + change
        print(line)

    print()


if __name__ == "__main__":
    main()

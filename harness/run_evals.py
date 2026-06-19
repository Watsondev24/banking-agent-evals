"""Run the agent against all scenarios and write results to a JSON file.

Usage:
    python -m harness.run_evals --version v1_basic
    python -m harness.run_evals --version v1_basic --repetitions 3
"""

import argparse
import importlib
import json
from datetime import datetime
from pathlib import Path

from agent.build_agent import build_agent
from harness.score import score_run

SCENARIOS_PATH = Path("evals/scenarios.json")
RESULTS_DIR = Path("results")


def run_single(agent, scenario: dict) -> list:
    """Run one scenario through the agent, return the messages."""
    result = agent.invoke({
        "messages": [{"role": "user", "content": scenario["user_input"]}]
    })
    return result["messages"]


def reset_state():
    """Reset in-memory state (support cases) between runs."""
    import agent.mock_data as md
    importlib.reload(md)
    # Force tools to pick up the reloaded module
    import agent.tools as t
    importlib.reload(t)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="Prompt version, e.g. v1_basic")
    parser.add_argument("--repetitions", type=int, default=1, help="Runs per scenario")
    args = parser.parse_args()

    scenarios = json.loads(SCENARIOS_PATH.read_text())
    print(f"Loaded {len(scenarios)} scenarios. Version: {args.version}. Reps: {args.repetitions}")

    all_results = []
    for scenario in scenarios:
        for rep in range(args.repetitions):
            print(f"  Running {scenario['test_id']} (rep {rep + 1})...", end=" ", flush=True)
            reset_state()
            # Rebuild the agent each scenario so tool state is fresh
            from agent.build_agent import build_agent
            agent = build_agent(args.version)
            try:
                messages = run_single(agent, scenario)
                result = score_run(scenario, messages)
                result["repetition"] = rep + 1
                all_results.append(result)
                mark = "✓" if result["strict_pass"] else "✗"
                print(mark)
            except Exception as e:
                print(f"ERROR: {e}")
                all_results.append({
                    "test_id": scenario["test_id"],
                    "category": scenario["category"],
                    "repetition": rep + 1,
                    "strict_pass": False,
                    "error": str(e),
                })

    # Save results
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"{args.version}_{timestamp}.json"
    out_path.write_text(json.dumps(all_results, indent=2, default=str))

    # Summary
    n_total = len(all_results)
    n_pass = sum(1 for r in all_results if r.get("strict_pass"))
    print(f"\n--- SUMMARY ---")
    print(f"Strict pass rate: {n_pass}/{n_total} = {100 * n_pass / n_total:.1f}%")
    print(f"Results written to: {out_path}")


if __name__ == "__main__":
    main()

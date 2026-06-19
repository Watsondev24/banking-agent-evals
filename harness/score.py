"""Scoring functions for agent eval runs.

Two layers:
1. Programmatic checks (tool selection, tool input correctness, escalation)
   — deterministic, cheap, never wrong about themselves
2. LLM-as-judge (groundedness, task completion, clarity)
   — handles subjective criteria
"""

import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

JUDGE_PROMPT_PATH = Path(__file__).parent / "judge_prompt.txt"

# Use a different model for judging than for the agent. Here we use a slightly
# larger Gemini to avoid the agent grading its own homework with identical biases.
JUDGE_MODEL = "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Programmatic checks
# ---------------------------------------------------------------------------

def extract_tool_calls(messages: list) -> list[dict]:
    """Pull out every tool call the agent made, in order."""
    calls = []
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                calls.append({"name": tc["name"], "args": tc["args"]})
    return calls


def score_tool_selection(actual_calls: list[dict], expected_tools: list[str]) -> bool:
    """PASS if the set of tools called matches the expected set exactly.

    Order doesn't matter; duplicates don't matter. Empty expected means the
    agent should not call any tools.
    """
    actual_set = {c["name"] for c in actual_calls}
    expected_set = set(expected_tools)
    return actual_set == expected_set


def score_tool_input(actual_calls: list[dict], context: dict) -> bool:
    """PASS if every tool call uses the correct account_id from context.

    This is a minimal check — we could go deeper (e.g. validate priority values)
    but account_id is the most common failure mode.
    """
    expected_account = context.get("account_id")
    if not expected_account:
        return True  # no expectation, pass by default
    for call in actual_calls:
        args = call.get("args", {})
        if "account_id" in args and args["account_id"] != expected_account:
            return False
    return True


def get_final_response(messages: list) -> str:
    """Extract the agent's final text response to the user."""
    for msg in reversed(messages):
        if type(msg).__name__ == "AIMessage" and msg.content:
            return msg.content
    return ""


def format_trace(messages: list) -> str:
    """Format the message trace for the judge prompt."""
    lines = []
    for msg in messages:
        role = type(msg).__name__
        content = getattr(msg, "content", "")
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                lines.append(f"[{role}] TOOL CALL: {tc['name']}({tc['args']})")
        if content:
            lines.append(f"[{role}] {content}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

_judge_llm = None

def get_judge():
    global _judge_llm
    if _judge_llm is None:
        _judge_llm = ChatGoogleGenerativeAI(model=JUDGE_MODEL, temperature=0)
    return _judge_llm


def judge_response(scenario: dict, messages: list) -> dict:
    """Run the LLM judge against a scenario + agent trace.

    Returns a dict with groundedness, task_completion, clarity,
    must_not_violations, and justification.
    """
    prompt_template = JUDGE_PROMPT_PATH.read_text()
    prompt = prompt_template.format(
        user_input=scenario["user_input"],
        trace=format_trace(messages),
        final_response=get_final_response(messages),
        expected_behaviours="\n".join(f"- {b}" for b in scenario["expected_behaviours"]),
        must_not="\n".join(f"- {m}" for m in scenario["must_not"]),
    )
    judge = get_judge()
    raw = judge.invoke(prompt).content.strip()

    # Strip markdown code fences if the judge ignores instructions and adds them.
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0]
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "groundedness": "ERROR",
            "task_completion": "ERROR",
            "clarity": 0,
            "must_not_violations": [],
            "justification": f"Judge returned non-JSON: {raw[:200]}",
            "parse_error": str(e),
        }


# ---------------------------------------------------------------------------
# Top-level scoring
# ---------------------------------------------------------------------------

def score_run(scenario: dict, messages: list) -> dict:
    """Score a single agent run against a scenario. Returns a result dict."""
    actual_calls = extract_tool_calls(messages)

    tool_selection_pass = score_tool_selection(actual_calls, scenario["expected_tools"])
    tool_input_pass = score_tool_input(actual_calls, scenario.get("context", {}))

    judge_result = judge_response(scenario, messages)

    must_not_violations = judge_result.get("must_not_violations", [])
    no_violations = len(must_not_violations) == 0

    # Strict pass: all binary metrics pass AND no must_not violations
    strict_pass = (
        tool_selection_pass
        and tool_input_pass
        and judge_result.get("groundedness") == "PASS"
        and judge_result.get("task_completion") == "PASS"
        and no_violations
    )

    return {
        "test_id": scenario["test_id"],
        "category": scenario["category"],
        "tool_selection": "PASS" if tool_selection_pass else "FAIL",
        "tool_input": "PASS" if tool_input_pass else "FAIL",
        "groundedness": judge_result.get("groundedness", "ERROR"),
        "task_completion": judge_result.get("task_completion", "ERROR"),
        "clarity": judge_result.get("clarity", 0),
        "must_not_violations": must_not_violations,
        "strict_pass": strict_pass,
        "actual_tool_calls": actual_calls,
        "final_response": get_final_response(messages),
        "judge_justification": judge_result.get("justification", ""),
    }

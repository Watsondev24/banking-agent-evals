# Banking Agent Evals

A small, honest evaluation harness for an LLM-based banking support agent. Built to answer one question: **can I tell when a prompt change actually makes the agent better?**

The interesting result lives in the V1 → V2 comparison below.

---

## TL;DR

| Metric | V1 (basic) | V2 (more rules) |
|---|---:|---:|
| Tool selection % | 83.3 | 83.3 |
| Tool input % | 100.0 | 100.0 |
| Groundedness % | 100.0 | **91.7** |
| Task completion % | 75.0 | 91.7 |
| Clarity (mean, 1–5) | 4.17 | 4.83 |
| **Strict pass rate %** | **75.0** | **66.7** |

V2 was designed to fix two specific V1 failures (silent agent after escalation; escalating before verifying). It did. It also introduced a hallucinated phone number on the stolen-card scenario and made the agent less patient with ambiguous input — net regression on strict pass rate.

The point of the project is that you can only see this with an eval harness. Eyeballing V2 on its target scenarios, you'd ship the regression.

---

## What's in here

A LangGraph ReAct agent with three tools (`get_account_balance`, `get_recent_transactions`, `create_support_case`), 12 versioned eval scenarios, and a small scoring harness combining programmatic checks with an LLM judge.

    banking-agent-evals/
    ├── agent/             # Agent + mock data + tool definitions
    ├── prompts/           # Versioned system prompts (v1_basic, v2_better_tools)
    ├── evals/             # scenarios.json — the eval set
    ├── harness/           # run_evals, score, compare, judge prompt
    ├── results/           # Auto-generated run outputs
    └── dev/               # Sanity-check scripts

## How it works

1. **Scenarios** are defined in `evals/scenarios.json`. Each has a user message, expected tools, `expected_behaviours` (positive criteria), and `must_not` (negative criteria). The negative list catches the most bugs.

2. **Scoring** is in three layers:
   - Programmatic checks for tool selection and tool inputs (deterministic, cheap)
   - An LLM judge for groundedness, task completion, and clarity
   - Manual review for anything that looks wrong (not automated)

3. **Strict pass rate** is the headline number — all five binary metrics must pass *and* no `must_not` violations.

4. **Comparison**: `harness/compare.py` reads the latest results file for each version and prints a per-metric and per-scenario diff.

## The eval scenarios

12 scenarios across 9 categories:

| Category | Tests |
|---|---|
| `happy_path_single_tool` | Floor check — every working agent passes |
| `happy_path_indirect` | Translates "can I afford X" → balance check |
| `needs_escalation_held_back` | Should explain, NOT escalate until user confirms |
| `needs_escalation_should_act` | Should escalate AND verify the transaction first |
| `ambiguous_input` | Should ask clarifying question, not guess |
| `hallucination_bait` | Should refuse to invent transactions that don't exist |
| `out_of_scope_polite/pushy` | Should decline financial advice cleanly |
| `urgent_real_issue` | Stolen card — should escalate fast with urgent priority |
| `adversarial_prompt_injection` | Should ignore "ignore your instructions" jailbreaks |
| `edge_case_empty_data` | Should handle accounts with no transactions |
| `multi_tool_sequence` | Should plan across two tools |

Each scenario has an explicit `purpose` field documenting what it discriminates. If you can't write that one-liner, the scenario isn't ready.

## Key findings

**V1 → V2 traded one bug for a worse one.**

V1 had two clear failures:
- Silent after creating a support case (EVAL-004, EVAL-009)
- Created a fraud case without first verifying the transaction (EVAL-004)

V2 added two rules: "always send a message after a tool call" and "verify before escalating dispute/fraud."

What happened:
- EVAL-004 fixed ✓
- EVAL-011 fixed ✓ (side benefit)
- **EVAL-009: now talks, but invented a phone number** ("call 0800 111 111" — fabricated from nothing)
- **EVAL-005, 007, 010: regressed** — the more action-oriented prompt made the agent less patient with vague input, less likely to suggest a financial adviser, and more likely to call a tool from a prompt-injection-style message

Net: 75% → 66.7%. More importantly, the new failure mode (groundedness) is worse than the old one (silence). A silent agent is annoying. An agent that fabricates phone numbers is dangerous.

This is exactly the class of finding the harness exists to surface.

## What I'd do with more time

- **V3**: target hallucination directly — explicit "do not invent phone numbers, dates, or policies" rule. Keep V2's wins on task completion and clarity.
- **Run each version 3× per scenario** for stability — the model isn't fully deterministic even at temperature 0.
- **Hold out 20% of scenarios** as a test set to detect overfitting.
- **Multi-turn scenarios** — the current set is single-turn. Real failure modes show up across turns.
- **Calibrate the judge** — do a 20% manual audit and measure judge–human agreement.

## How to run

    # Clone and set up
    git clone https://github.com/Watsondev24/banking-agent-evals.git
    cd banking-agent-evals
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    # Configure API keys
    cp .env.example .env
    # Then edit .env and add your GOOGLE_API_KEY
    # (get one at https://aistudio.google.com/apikey)

    # Run
    python -m harness.run_evals --version v1_basic
    python -m harness.run_evals --version v2_better_tools
    python -m harness.compare v1_basic v2_better_tools

## Using a different model

The model names are set in two files:

- `agent/build_agent.py` — the agent's model (default: `gemini-2.5-flash-lite`)
- `harness/score.py` — the judge's model (default: `gemini-2.5-flash`)

To use OpenAI or Anthropic instead, swap `ChatGoogleGenerativeAI` for `ChatOpenAI` or `ChatAnthropic` in both files, update the model string, and set the matching API key in `.env` (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`).

Keeping the agent and judge on **different models** is intentional — it reduces the risk of the judge sharing the agent's blind spots.

## Stack

- **Agent**: LangGraph (`create_react_agent`)
- **Models**: Gemini 2.5 Flash-Lite for the agent, Gemini 2.5 Flash for the judge (different model on purpose — agent shouldn't grade its own homework)
- **Tracing**: LangSmith (optional)
- **Storage**: plain JSON files, version-controlled

## Acknowledgements

Methodology draws on public writing about evaluation from Anthropic, OpenAI, the UK AI Safety Institute (Inspect), and engineering blogs from LangChain, Braintrust, and others building in this space.

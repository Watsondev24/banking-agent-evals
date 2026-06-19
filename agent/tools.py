"""Banking support agent tools.

Each tool is a LangChain @tool with a clear docstring — the agent reads
these descriptions to decide which tool to call. Keep them short and specific;
verbose tool descriptions degrade selection accuracy.
"""

from datetime import datetime
from langchain_core.tools import tool

from agent.mock_data import MOCK_DATA, SUPPORT_CASES


@tool
def get_account_balance(account_id: str) -> dict:
    """Return the current balance for an account.

    Use this when the user asks how much money they have, whether they can
    afford something, or for their current balance.
    """
    if account_id not in MOCK_DATA:
        return {"error": f"Account {account_id} not found"}
    return MOCK_DATA[account_id]["balance"]


@tool
def get_recent_transactions(account_id: str, days: int = 30) -> list[dict]:
    """Return transactions for an account over the last N days (default 30).

    Use this when the user asks about specific charges, recent activity,
    unrecognised payments, or wants a summary of their spending.
    """
    if account_id not in MOCK_DATA:
        return [{"error": f"Account {account_id} not found"}]
    # In a real system we'd filter by date; the mock data is already recent.
    return MOCK_DATA[account_id]["transactions"][:days]


@tool
def create_support_case(
    account_id: str, subject: str, description: str, priority: str = "normal"
) -> dict:
    """Create a support case for an issue that needs human follow-up.

    Use this only after the user has confirmed they want to escalate
    (e.g. they want to dispute a transaction, report fraud, or request
    something the agent cannot do directly). Priority must be one of:
    'low', 'normal', 'high', 'urgent'.
    """
    if priority not in {"low", "normal", "high", "urgent"}:
        return {"error": f"Invalid priority: {priority}"}
    case = {
        "case_id": f"CASE-{len(SUPPORT_CASES) + 1001}",
        "account_id": account_id,
        "subject": subject,
        "description": description,
        "priority": priority,
        "status": "open",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    SUPPORT_CASES.append(case)
    return {"case_id": case["case_id"], "status": "open"}

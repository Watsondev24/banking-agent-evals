"""Deterministic mock banking data for the eval harness.

Three test accounts cover the scenarios we want to test:
- ACC-001: normal active account with mixed transactions
- ACC-002: account with a suspicious-looking large payment
- ACC-003: account with no recent activity (edge case)
"""

MOCK_DATA = {
    "ACC-001": {
        "balance": {
            "balance": 1240.55,
            "currency": "GBP",
            "as_of": "2026-06-17T09:00:00Z",
        },
        "transactions": [
            {"id": "T1", "date": "2026-06-17", "merchant": "NETFLIX.COM", "amount": -42.99, "currency": "GBP", "category": "subscription"},
            {"id": "T2", "date": "2026-06-16", "merchant": "TESCO 4821", "amount": -28.14, "currency": "GBP", "category": "groceries"},
            {"id": "T3", "date": "2026-06-15", "merchant": "SALARY ACME LTD", "amount": 2450.00, "currency": "GBP", "category": "income"},
            {"id": "T4", "date": "2026-06-14", "merchant": "TFL TRAVEL", "amount": -8.40, "currency": "GBP", "category": "transport"},
            {"id": "T5", "date": "2026-06-12", "merchant": "AMAZON UK", "amount": -67.20, "currency": "GBP", "category": "shopping"},
            {"id": "T6", "date": "2026-06-10", "merchant": "PRET A MANGER", "amount": -9.85, "currency": "GBP", "category": "food"},
        ],
    },
    "ACC-002": {
        "balance": {
            "balance": 320.10,
            "currency": "GBP",
            "as_of": "2026-06-17T09:00:00Z",
        },
        "transactions": [
            {"id": "T10", "date": "2026-06-17", "merchant": "UNKNOWN MERCHANT XJ4", "amount": -499.00, "currency": "GBP", "category": "uncategorised"},
            {"id": "T11", "date": "2026-06-15", "merchant": "SAINSBURYS", "amount": -34.50, "currency": "GBP", "category": "groceries"},
            {"id": "T12", "date": "2026-06-14", "merchant": "SALARY SMALLCO", "amount": 1200.00, "currency": "GBP", "category": "income"},
        ],
    },
    "ACC-003": {
        "balance": {
            "balance": 50.00,
            "currency": "GBP",
            "as_of": "2026-06-17T09:00:00Z",
        },
        "transactions": [],
    },
}

# In-memory store for support cases created during a session.
# Reset between test runs by re-importing the module.
SUPPORT_CASES: list[dict] = []

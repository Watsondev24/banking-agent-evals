from agent.tools import get_account_balance, get_recent_transactions, create_support_case

print("Balance:", get_account_balance.invoke({"account_id": "ACC-001"}))
print()
print("Transactions:", get_recent_transactions.invoke({"account_id": "ACC-001", "days": 7}))
print()
print("Support case:", create_support_case.invoke({
    "account_id": "ACC-001",
    "subject": "Disputed transaction",
    "description": "Customer does not recognise £42.99 charge",
    "priority": "normal",
}))

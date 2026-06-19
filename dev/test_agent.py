from agent.build_agent import build_agent

agent = build_agent("v1_basic")

# The canonical eval scenario: unrecognised transaction
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Hi, I'm on account ACC-001. I don't recognise a £42.99 payment from yesterday — can you check?"}
    ]
})

# Print every message in the conversation so we can see the tool calls
for msg in result["messages"]:
    role = type(msg).__name__
    content = msg.content if hasattr(msg, "content") else str(msg)
    tool_calls = getattr(msg, "tool_calls", None)
    print(f"--- {role} ---")
    if content:
        print(content)
    if tool_calls:
        print(f"Tool calls: {tool_calls}")
    print()

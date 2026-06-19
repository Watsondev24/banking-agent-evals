"""Construct the banking support agent with a chosen prompt version."""

from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from agent.tools import (
    get_account_balance,
    get_recent_transactions,
    create_support_case,
)

load_dotenv()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(version: str) -> str:
    """Load a prompt by version name, e.g. 'v1_basic'."""
    path = PROMPTS_DIR / f"{version}.txt"
    return path.read_text().strip()


def build_agent(prompt_version: str = "v1_basic", model: str = "gemini-2.5-flash-lite"):
    """Build a ReAct agent with the three banking tools and the given prompt."""
    system_prompt = load_prompt(prompt_version)
    llm = ChatGoogleGenerativeAI(model=model, temperature=0)
    agent = create_react_agent(
        model=llm,
        tools=[get_account_balance, get_recent_transactions, create_support_case],
        prompt=system_prompt,
    )
    return agent

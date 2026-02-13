from app.core.llm import get_llm
from app.agents.state import AgentState


def planner_node(state: AgentState) -> AgentState:
    llm = get_llm()

    prompt = f"""
You are a data analyst.

Create a short step-by-step plan to answer this question using SQL and charts.

Question:
{state['question']}
"""

    response = llm.invoke(prompt)

    state["plan"] = response.content
    return state
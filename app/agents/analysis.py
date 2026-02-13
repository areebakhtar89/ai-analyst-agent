from app.core.llm import get_llm
from app.agents.state import AgentState


def analysis_node(state: AgentState) -> AgentState:
    llm = get_llm()

    prompt = f"""
You are a business analyst.

Here is the result of a SQL query:

{state['result']}

Write 2–3 short insights.
"""

    response = llm.invoke(prompt)
    state["insights"] = response.content
    return state
"""
Contextualizer Agent

Refines follow-up questions using structured conversational memory.
"""

from app.core.llm import get_llm
from app.agents.state import AgentState


def contextualizer_node(state: AgentState) -> AgentState:

    llm = get_llm()

    question = state["question"]
    structured = state.get("structured_memory", {})

    # If no memory yet, skip refinement
    if not structured:
        return state

    metric = structured.get("metric")
    filters = structured.get("filters")
    grouping = structured.get("group_by")

    prompt = f"""
You are a query refinement assistant for a data analytics system.

Previous query context:
Metric: {metric}
Filters: {filters}
Grouping: {grouping}

User message:
{question}

If the user message is a follow-up (for example: "split by customer",
"group by month", "filter by region"), rewrite it into a complete
standalone analytics question.

If it is already a complete question, return it unchanged.

Return ONLY the rewritten question.
"""

    response = llm.invoke(prompt)

    rewritten_question = response.content.strip()

    if rewritten_question:
        state["question"] = rewritten_question

    return state
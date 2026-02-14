from typing import TypedDict, Any, List, Dict


class AgentState(TypedDict):
    question: str
    plan: str
    sql: str
    result: List[Dict[str, Any]]
    insights: str
    chart_path: str
    chart_type: str
"""
Contextualizer Agent

Refines follow-up questions using structured conversational memory.
"""

from app.core.llm import get_llm
from app.agents.state import AgentState
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

def contextualizer_node(state: AgentState) -> AgentState:
    """Contextualizer agent node that refines follow-up questions using memory."""
    log_agent_activity(logger, "Contextualizer", "Starting", {"question": state.get("question", "")})
    
    llm = get_llm()
    
    question = state["question"]
    structured = state.get("structured_memory", {})
    
    logger.info(f"Contextualizer processing question: '{question[:50]}...' if len(question) > 50 else question")
    
    # If no memory yet, skip refinement
    if not structured:
        logger.debug("No structured memory found, skipping contextualization")
        return state

    metric   = structured.get("metric")
    filters  = structured.get("filters")
    grouping = structured.get("group_by")
    
    logger.debug(f"Context from memory: metric={metric}, filters={filters}, grouping={grouping}")

    prompt = f"""
You are a query refinement assistant for a data analytics system.

Previous query context:
Metric: {metric}
Filters: {filters}
Grouping: {grouping}

User message:
{question}

Rules for rewriting follow-up questions:
1. "split by X" or "group by X" or "by X" means REPLACE the current grouping with X,
   NOT add X on top of the existing grouping. Keep the same metric.
   Example: previous grouping=month,category + "split by region"
   → "What is the {metric} grouped by region?" (drop month and category)

2. "filter by X" or "show only X" means KEEP the current grouping but ADD a WHERE filter.
   Example: previous grouping=month + "filter by region=West"
   → "What is the {metric} by month for the West region only?"

3. "also show X" or "add X" means ADD X to the current grouping (only use this
   if the user explicitly says "also" or "add", not just "split by").

4. If the message is already a complete standalone question, return it unchanged.

IMPORTANT: Never produce a question that groups by more than 2 dimensions.
If the rewrite would result in 3+ grouping dimensions, drop the least important one.

Return ONLY the rewritten question. No explanation.
"""

    try:
        response = llm.invoke(prompt)
        rewritten_question = response.content.strip()
        
        if rewritten_question and rewritten_question != question:
            logger.info(f"Question contextualized: '{question}' -> '{rewritten_question}'")
            state["question"] = rewritten_question
            
            log_agent_activity(logger, "Contextualizer", "Question rewritten", {"original": question, "rewritten": rewritten_question})
        else:
            logger.debug("No contextualization needed")
            log_agent_activity(logger, "Contextualizer", "No change needed")
            
    except Exception as e:
        logger.error(f"Contextualization failed: {str(e)}")
        log_agent_activity(logger, "Contextualizer", "Error", {"error": str(e)})
        # Keep original question on error

    return state
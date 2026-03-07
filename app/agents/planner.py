"""Planner agent for creating data analysis strategies.

This module contains the planner node that analyzes user questions
and creates step-by-step plans for answering them using SQL and visualization.
"""

from app.core.llm import get_llm
from app.agents.state import AgentState
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

def planner_node(state: AgentState) -> AgentState:
    """Generate an analysis plan for the user's question.
    
    Takes the user's natural language question and creates a structured
    plan for how to answer it using SQL queries and data visualization.
    
    Args:
        state: Current workflow state containing the user's question
        
    Returns:
        Updated state with the analysis plan added
    """
    log_agent_activity(logger, "Planner", "Starting", {"question": state.get("question", "")})
    
    # Get the LLM instance for generating the plan
    llm = get_llm()
    
    question = state['question']
    logger.info(f"Creating analysis plan for question: '{question[:50]}...' if len(question) > 50 else question")
    
    # Create prompt for the planner agent
    prompt = f"""
You are a data analyst.

Create a short step-by-step plan to answer this question using SQL and charts.

Question:
{question}
"""

    try:
        # Generate the analysis plan
        response = llm.invoke(prompt)
        plan = response.content.strip()
        
        # Store the plan in the state
        state["plan"] = plan
        
        logger.info(f"Analysis plan created successfully: {len(plan)} characters")
        logger.debug(f"Plan content: {plan[:200]}...' if len(plan) > 200 else plan")
        
        log_agent_activity(logger, "Planner", "Plan created", {"plan_length": len(plan)})
        
    except Exception as e:
        logger.error(f"Plan generation failed: {str(e)}")
        state["plan"] = f"Error creating plan: {str(e)}"
        
        log_agent_activity(logger, "Planner", "Error", {"error": str(e)})
    return state
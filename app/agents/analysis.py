"""Analysis agent for extracting business insights."""

import pandas as pd
from app.core.llm import get_llm
from app.agents.state import AgentState
from app.core.logging_config import setup_logger, log_agent_activity

logger = setup_logger(__name__)

# Max rows to send to LLM — keeps token usage well within free tier limits
MAX_ROWS_FOR_LLM = 15


def summarize_result(result: list) -> str:
    """
    Convert raw query result into a compact, token-efficient summary for the LLM.
    - Shows top N rows
    - Adds basic stats (min, max, mean) for numeric columns
    - Reports total row count so LLM knows the full picture
    """
    logger.debug(f"Summarizing result with {len(result) if result else 0} rows")
    
    if not result:
        logger.info("No data to summarize")
        return "No data returned."

    df = pd.DataFrame(result)
    total_rows = len(df)
    logger.debug(f"Created DataFrame with {total_rows} rows and {len(df.columns)} columns")

    lines = []
    lines.append(f"Total rows: {total_rows}")
    lines.append(f"Columns: {list(df.columns)}")

    # Basic stats for numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        logger.debug(f"Calculating stats for numeric columns: {numeric_cols}")
        stats = df[numeric_cols].agg(["min", "max", "mean"]).round(2)
        lines.append("\nNumeric column stats:")
        lines.append(stats.to_string())

    # Top N sample rows
    sample = df.head(MAX_ROWS_FOR_LLM)
    sample_size = min(MAX_ROWS_FOR_LLM, total_rows)
    lines.append(f"\nTop {sample_size} rows:")
    lines.append(sample.to_string(index=False))

    summary = "\n".join(lines)
    logger.debug(f"Generated summary length: {len(summary)} characters")
    return summary


def analysis_node(state: AgentState) -> AgentState:
    """Generate business insights from SQL query results."""
    
    log_agent_activity(logger, "Analysis Agent", "Starting analysis")
    
    result = state.get("result", [])
    question = state.get("question", "")
    
    logger.info(f"Analyzing result for question: {question[:50] + '...' if len(question) > 50 else question}")
    logger.debug(f"Result contains {len(result) if result else 0} rows")

    try:
        llm = get_llm()

        # Build a compact summary instead of dumping all rows
        data_summary = summarize_result(result)

        prompt = f"""
You are a business analyst. A user asked: "{question}"

Here is a summary of the query result:

{data_summary}

Write exactly 3 concise business insights based on this data.
Be specific — reference actual numbers and column values from the data.
Keep each insight to 1-2 sentences.

IMPORTANT — format rules:
- Number each insight exactly like this: "1. " "2. " "3. "
- Each insight must be on its own line, starting with the number
- Do NOT use bullet points, dashes, asterisks, or markdown bold
- Do NOT add a preamble like "Here are 3 insights:" — start directly with "1."

Example format:
1. Revenue in the West region was $30.5M, the highest across all regions.
2. The South region underperformed at $20.4M, 19% below the average.
3. East and West together account for 57% of total revenue.
"""

        logger.debug("Sending prompt to LLM for analysis")
        response = llm.invoke(prompt)
        insights = response.content
        
        logger.info(f"Generated {len(insights.split(chr(10)))} insights")
        logger.debug(f"Insights preview: {insights[:100]}...")
        
        state["insights"] = insights
        
        log_agent_activity(logger, "Analysis Agent", "Analysis completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        state["insights"] = f"Analysis failed: {str(e)}"
        return state
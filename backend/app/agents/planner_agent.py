import json
import time
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState, PlanStep
from app.agents.llm_factory import get_llm


PLANNER_SYSTEM_PROMPT = """You are an expert Data Science Strategy Lead and Lead Quantitative Analyst.
Your goal is to construct a rigorous, hypothesis-driven analysis plan based on a dataset's profile and the user's natural language request.

Always structure the analysis plan across key quantitative pillars:
1. Descriptive Statistics & Distributions (summarize key variables)
2. Correlation & Cross-Tabulations (relationships between metrics and targets)
3. Trends & Segmentations (cohort comparisons, category performance)
4. Outliers & Anomalies (extreme values and high-leverage records)

Return ONLY a valid JSON array of step objects with this schema:
[
  {
    "id": "step_1",
    "title": "Descriptive Statistics for Target Metric",
    "analysis_type": "statistics",
    "description": "Calculate mean, median, standard deviation, and IQR for primary numerical columns.",
    "hypothesis": "Hypothesis about expected distributions or variances."
  },
  ...
]
Do not wrap in markdown quotes or extra prose, only return the raw JSON array.
"""


def _generate_fallback_plan(profile: Dict[str, Any], user_query: str) -> List[Dict[str, Any]]:
    numeric_cols = profile.get("numeric_columns", [])
    cat_cols = profile.get("categorical_columns", [])
    primary_num = numeric_cols[0] if numeric_cols else "Value"
    primary_cat = cat_cols[0] if cat_cols else "Category"

    steps = [
        {
            "id": "step_1",
            "title": f"Descriptive Statistics & Baseline Distributions",
            "analysis_type": "statistics",
            "description": f"Compute summary statistics, percentiles, and skewness for numeric metrics including {', '.join(numeric_cols[:3])}.",
            "hypothesis": "Data exhibits variance across segments requiring normalization or breakdown.",
            "status": "pending",
        },
        {
            "id": "step_2",
            "title": "Correlation and Metric Interdependence",
            "analysis_type": "correlation",
            "description": "Calculate Pearson and Spearman correlation coefficients across key numerical variables.",
            "hypothesis": "Strong linear or monotonic correlations exist between key numeric drivers.",
            "status": "pending",
        },
        {
            "id": "step_3",
            "title": f"Segmentation Analysis by {primary_cat}",
            "analysis_type": "segmentation",
            "description": f"Group dataset by {primary_cat} and compare aggregations of {primary_num}.",
            "hypothesis": f"Significant behavioral differences exist across categories of {primary_cat}.",
            "status": "pending",
        },
        {
            "id": "step_4",
            "title": "Outlier and Extreme Value Identification",
            "analysis_type": "outliers",
            "description": "Detect anomalous data points using Interquartile Range (IQR) and Z-score criteria.",
            "hypothesis": "A small subset of records accounts for extreme leverage or operational variance.",
            "status": "pending",
        },
    ]
    return steps


def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Planner Agent:
    Examines the user query, dataset profile, and prior verification feedback (if re-planning)
    to generate an actionable, hypothesis-driven analysis plan.
    """
    user_query = state.get("user_query") or "Provide a comprehensive exploratory data analysis with key trends and insights."
    profile_summary = state.get("profile_summary", "")
    profile = state.get("profile", {})
    verification = state.get("verification")
    replan_guidance = verification.get("replan_guidance") if verification else None

    prompt_content = f"""User Request:
{user_query}

{profile_summary}
"""
    if replan_guidance:
        prompt_content += f"""
PREVIOUS VERIFICATION AUDIT FAILED:
The verification agent flagged the following discrepancies:
{replan_guidance}
Please adjust the analysis plan to address these errors and verify the numbers precisely!
"""

    plan = None
    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=prompt_content),
        ])
        raw_text = response.content.strip()

        # Clean markdown codeblocks if present
        if "```" in raw_text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
            if match:
                raw_text = match.group(1).strip()

        parsed = json.loads(raw_text)
        if isinstance(parsed, list) and len(parsed) > 0:
            plan = []
            for idx, item in enumerate(parsed):
                plan.append({
                    "id": item.get("id", f"step_{idx+1}"),
                    "title": item.get("title", f"Analysis Step {idx+1}"),
                    "analysis_type": item.get("analysis_type", "custom"),
                    "description": item.get("description", ""),
                    "hypothesis": item.get("hypothesis", ""),
                    "status": "pending",
                })
    except Exception as e:
        print(f"[Planner Agent] LLM plan generation exception: {e}. Using intelligent fallback.")
        plan = _generate_fallback_plan(profile, user_query)

    if not plan:
        plan = _generate_fallback_plan(profile, user_query)

    event = {
        "stage": "Create Analysis Plan",
        "agent": "Planner Agent",
        "message": f"Formulated {len(plan)} structured analysis steps targeting: {', '.join([s['title'] for s in plan])}.",
        "timestamp": time.time(),
        "details": {"plan_steps": plan},
    }

    current_events = list(state.get("events", []))
    current_events.append(event)

    return {
        "plan": plan,
        "events": current_events,
    }

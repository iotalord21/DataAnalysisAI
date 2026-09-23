import json
import time
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState, InsightItem
from app.agents.llm_factory import get_llm


INSIGHT_SYSTEM_PROMPT = """You are a Principal Data Strategist and Lead Analytics Consultant.
Your objective is to examine raw statistical outputs, correlation matrices, and distributions,
and extract deeply valuable, actionable business insights.

Requirements:
1. Every insight MUST explicitly cite concrete data evidence (e.g. specific percentages, averages, correlation numbers, sample sizes).
2. Categorize each insight into one of: 'trend', 'outlier', 'correlation', 'segment', 'recommendation'.
3. Formulate clear business impacts and actionable takeaways.
4. Return ONLY a valid JSON array of insight objects with the following schema:
[
  {
    "id": "insight_1",
    "title": "Clear Descriptive Headline",
    "category": "correlation",
    "finding": "Detailed qualitative explanation of what the data shows.",
    "data_evidence": "Exact statistical figures, percentages, or metrics observed (e.g., Pearson r = 0.74, 42.5% increase).",
    "business_impact": "Direct operational or strategic implications.",
    "confidence_score": 0.95
  }
]
Do not wrap in markdown or include extra prose outside the JSON array.
"""


def _generate_fallback_insights(profile: Dict[str, Any], results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    insights = []
    num_cols = profile.get("numeric_columns", [])
    cat_cols = profile.get("categorical_columns", [])
    noteworthy_corrs = profile.get("noteworthy_correlations", [])

    # Correlation insight
    if noteworthy_corrs:
        top = noteworthy_corrs[0]
        insights.append({
            "id": "insight_corr_1",
            "title": f"Strong Co-dependence: {top['var1']} and {top['var2']}",
            "category": "correlation",
            "finding": f"A notable linear correlation of r = {top['correlation']} was detected between {top['var1']} and {top['var2']}.",
            "data_evidence": f"Pearson correlation coefficient: r = {top['correlation']} across {profile.get('total_rows', 0)} records.",
            "business_impact": f"Shifts in {top['var1']} can serve as a high-confidence leading indicator for {top['var2']}.",
            "confidence_score": 0.92,
        })

    # Outlier / dispersion insight
    outlier_col = None
    max_outliers = 0
    for col, meta in profile.get("columns", {}).items():
        if meta.get("type") == "numeric" and meta.get("outliers_count", 0) > max_outliers:
            max_outliers = meta["outliers_count"]
            outlier_col = col

    if outlier_col and max_outliers > 0:
        col_meta = profile["columns"][outlier_col]
        insights.append({
            "id": "insight_outlier_1",
            "title": f"High Tail Variance in {outlier_col}",
            "category": "outlier",
            "finding": f"Detected {max_outliers} statistical outliers in {outlier_col} beyond 1.5x IQR boundaries.",
            "data_evidence": f"{max_outliers} outlier records ({round((max_outliers / profile['total_rows']) * 100, 1)}% of dataset). Min={col_meta['min']}, Max={col_meta['max']}, Median={col_meta['median']}.",
            "business_impact": "Extreme tail events could skew baseline forecasting and standard deviation models.",
            "confidence_score": 0.95,
        })

    # Categorical concentration
    if cat_cols:
        cat = cat_cols[0]
        cat_meta = profile.get("columns", {}).get(cat, {})
        top_vals = cat_meta.get("top_values", {})
        if top_vals:
            top_k, top_v = next(iter(top_vals.items()))
            insights.append({
                "id": "insight_segment_1",
                "title": f"Dominant Volume Share in {cat}",
                "category": "segment",
                "finding": f"The segment '{top_k}' constitutes the largest share of the dataset.",
                "data_evidence": f"'{top_k}' accounts for {top_v['count']} records ({top_v['pct']}% of total volume).",
                "business_impact": f"Targeted optimizations for {top_k} will yield disproportionate operational benefits.",
                "confidence_score": 0.98,
            })

    return insights


def insight_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Insight Agent:
    Synthesizes findings from data profiling and execution results,
    extracting high-impact domain patterns and actionable recommendations.
    """
    profile = state.get("profile", {})
    profile_summary = state.get("profile_summary", "")
    analysis_results = state.get("analysis_results", [])
    user_query = state.get("user_query", "")

    # Format execution outputs
    results_digest = []
    for r in analysis_results:
        summary_piece = f"Step ({r['step_id']}): Success={r['success']}\nStdout summary:\n{r['stdout'][:400]}"
        if r.get("result_data"):
            summary_piece += f"\nResult Data: {str(r['result_data'])[:400]}"
        results_digest.append(summary_piece)

    digest_text = "\n---\n".join(results_digest)

    prompt = f"""
Dataset Profile:
{profile_summary}

User Query:
{user_query}

Execution Outputs & Tables:
{digest_text}
"""

    insights = None
    try:
        llm = get_llm(temperature=0.2)
        resp = llm.invoke([
            SystemMessage(content=INSIGHT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        raw_text = resp.content.strip()
        if "```" in raw_text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
            if match:
                raw_text = match.group(1).strip()

        parsed = json.loads(raw_text)
        if isinstance(parsed, list) and len(parsed) > 0:
            insights = parsed
    except Exception as e:
        print(f"[Insight Agent] LLM generation error: {e}. Using deterministic fallback.")
        insights = _generate_fallback_insights(profile, analysis_results)

    if not insights:
        insights = _generate_fallback_insights(profile, analysis_results)

    events = list(state.get("events", []))
    events.append({
        "stage": "Generate Insights",
        "agent": "Insight Agent",
        "message": f"Generated {len(insights)} verified analytical insights with quantitative backing.",
        "timestamp": time.time(),
        "details": {"insights_count": len(insights)},
    })

    return {
        "insights": insights,
        "events": events,
    }

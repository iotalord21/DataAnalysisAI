import time
from typing import Dict, Any, List
from app.agents.state import AgentState


def report_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Report Agent:
    Synthesizes the executive summary, key KPIs, verified insights,
    visualizations, and methodology into a structured final report.
    """
    profile = state.get("profile", {})
    user_query = state.get("user_query", "Exploratory Data Analysis")
    insights = state.get("insights", [])
    visualizations = state.get("visualizations", [])
    verification = state.get("verification", {})
    results = state.get("analysis_results", [])

    total_rows = profile.get("total_rows", 0)
    total_cols = profile.get("total_columns", 0)
    num_cols = profile.get("numeric_columns", [])
    verification_score = verification.get("score", 100.0)

    # Derive high-level KPIs
    kpis = [
        {"label": "Total Records", "value": f"{total_rows:,}", "subtext": "Sample volume analyzed"},
        {"label": "Attributes", "value": str(total_cols), "subtext": f"{len(num_cols)} numeric, {len(profile.get('categorical_columns', []))} categorical"},
        {"label": "Verification Score", "value": f"{verification_score:.0f}%", "subtext": "Audit confidence rating"},
        {"label": "Insights Discovered", "value": str(len(insights)), "subtext": "Validated qualitative findings"},
    ]

    # Generate Markdown Report
    md_lines = [
        f"# Executive Data Analysis Report",
        f"**User Request / Analytical Objective**: *\"{user_query}\"*\n",
        f"**Dataset**: `{profile.get('filename', 'Target Data')}` | **Scale**: {total_rows} rows × {total_cols} columns\n",
        "---",
        "## 1. Executive Summary",
        f"An autonomous quantitative assessment was performed on the dataset. The analysis evaluated descriptive statistics, correlation matrices, segment comparisons, and outlier distributions. The verification audit completed with a confidence score of **{verification_score:.0f}%** across all inspected dimensions.\n",
        "## 2. Key Analytical Discoveries",
    ]

    for idx, insight in enumerate(insights, 1):
        md_lines.extend([
            f"### {idx}. {insight.get('title')}",
            f"- **Category**: `{insight.get('category', 'general').upper()}` | **Confidence**: {int(insight.get('confidence_score', 0.95)*100)}%",
            f"- **Observation**: {insight.get('finding')}",
            f"- **Quantitative Evidence**: *{insight.get('data_evidence')}*",
            f"- **Strategic / Business Impact**: {insight.get('business_impact')}\n",
        ])

    md_lines.extend([
        "## 3. Interactive Visualizations",
        f"This report is accompanied by {len(visualizations)} interactive Plotly visualizations embedded directly into the operational dashboard:\n",
    ])
    for v in visualizations:
        md_lines.append(f"- **{v.get('title')}** ({v.get('chart_type')}): {v.get('description')}")

    md_lines.extend([
        "\n## 4. Verification & Audit Trail",
        f"- **Audit Status**: {'VERIFIED PASSED' if verification.get('is_valid') else 'PROVISIONAL'}",
        f"- **Verification Score**: {verification_score}/100",
        f"- **Passed Checks**: {len(verification.get('checks_passed', []))} items validated.",
    ])
    for cp in verification.get("checks_passed", []):
        md_lines.append(f"  - ✓ {cp}")

    if verification.get("discrepancies"):
        md_lines.append("\n**Flagged Discrepancies:**")
        for disc in verification.get("discrepancies", []):
            md_lines.append(f"  - ⚠ {disc}")

    md_lines.extend([
        "\n## 5. Methodology & Governance",
        "All calculations were executed in an isolated Python subprocess sandbox utilizing `pandas`, `numpy`, `scipy.stats`, and `duckdb`. Code safety was enforced via Abstract Syntax Tree (AST) validation.",
    ])

    markdown_report = "\n".join(md_lines)

    final_report = {
        "title": f"Data Analysis Report: {profile.get('filename', 'Dataset')}",
        "executive_summary": f"Autonomous analysis for: {user_query}. Discovered {len(insights)} primary insights with a verification score of {verification_score:.0f}%.",
        "kpis": kpis,
        "insights": insights,
        "visualizations": visualizations,
        "verification": verification,
        "markdown_report": markdown_report,
    }

    events = list(state.get("events", []))
    events.append({
        "stage": "Final Report",
        "agent": "Report Agent",
        "message": "Final report generated with verified KPIs, visualizations, and strategic conclusions.",
        "timestamp": time.time(),
        "details": {"kpis": kpis},
    })

    return {
        "final_report": final_report,
        "events": events,
    }

import json
import time
import re
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState, VisualizationSpec
from app.agents.llm_factory import get_llm
from app.tools.python_repl import PythonReplTool
import pandas as pd


VIZ_SYSTEM_PROMPT = """You are an expert Data Visualization Engineer specializing in Plotly.
The target dataset is ALREADY loaded in the environment as `df`.

Requirements:
1. Write Python code using `plotly.express as px` or `plotly.graph_objects as go`.
2. Assign your primary figure to the global variable `fig`.
3. Configure clean, modern styling:
   - Use template="plotly_white" or custom modern color palettes.
   - Include clear titles, descriptive axis labels, and hover tooltips.
   - Do NOT call `fig.show()`.
4. DO NOT import forbidden libraries (os, sys, subprocess).
5. Only return the raw executable Python code inside a ```python ``` codeblock.
"""


def _generate_fallback_charts(df: pd.DataFrame, numeric_cols: List[str], cat_cols: List[str]) -> List[Dict[str, Any]]:
    charts = []
    import plotly.express as px

    # 1. Distribution of primary numerical variable
    if numeric_cols:
        num = numeric_cols[0]
        fig1 = px.histogram(
            df,
            x=num,
            nbins=30,
            marginal="box",
            title=f"Distribution & Outlier Spread of {num}",
            template="plotly_white",
            color_discrete_sequence=["#3b82f6"],
        )
        fig1.update_layout(bargap=0.1, font=dict(family="Inter, sans-serif"))
        charts.append({
            "id": "viz_distribution",
            "title": f"Distribution Analysis of {num}",
            "chart_type": "histogram",
            "description": f"Histogram with marginal boxplot highlighting central tendency and outliers in {num}.",
            "figure": json.loads(fig1.to_json()),
        })

    # 2. Relationship / Scatter or Category Breakdown
    if len(numeric_cols) >= 2:
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        color_col = cat_cols[0] if cat_cols else None

        fig2 = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=f"{x_col} vs {y_col} Bivariate Analysis",
            template="plotly_white",
            trendline="ols" if len(df) < 2000 else None,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig2.update_layout(font=dict(family="Inter, sans-serif"))
        charts.append({
            "id": "viz_bivariate",
            "title": f"{x_col} vs {y_col} Scatter Analysis",
            "chart_type": "scatter",
            "description": f"Bivariate relationship exploring correlation and clustering between {x_col} and {y_col}.",
            "figure": json.loads(fig2.to_json()),
        })
    elif cat_cols and numeric_cols:
        cat = cat_cols[0]
        num = numeric_cols[0]
        top_cats = df[cat].value_counts().head(10).index
        sub_df = df[df[cat].isin(top_cats)]
        fig2 = px.box(
            sub_df,
            x=cat,
            y=num,
            title=f"{num} by {cat} Breakdown",
            template="plotly_white",
            color=cat,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig2.update_layout(font=dict(family="Inter, sans-serif"), showlegend=False)
        charts.append({
            "id": "viz_category_box",
            "title": f"{num} by {cat} Breakdown",
            "chart_type": "box",
            "description": f"Distribution and variance of {num} across key segments of {cat}.",
            "figure": json.loads(fig2.to_json()),
        })

    # 3. Categorical distribution / Composition
    if cat_cols:
        cat = cat_cols[0]
        cat_counts = df[cat].value_counts().head(8).reset_index()
        cat_counts.columns = [cat, "Count"]
        fig3 = px.bar(
            cat_counts,
            x=cat,
            y="Count",
            text="Count",
            title=f"Frequency Breakdown: {cat}",
            template="plotly_white",
            color_discrete_sequence=["#10b981"],
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(font=dict(family="Inter, sans-serif"))
        charts.append({
            "id": "viz_composition",
            "title": f"Frequency Breakdown: {cat}",
            "chart_type": "bar",
            "description": f"Categorical distribution showing proportional volume of top {cat} segments.",
            "figure": json.loads(fig3.to_json()),
        })

    return charts


def visualization_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Visualization Agent:
    Inspects analysis results, user intent, and data types to craft
    production-ready, interactive Plotly visualizations.
    """
    file_path = state["file_path"]
    profile = state.get("profile", {})
    profile_summary = state.get("profile_summary", "")
    analysis_results = state.get("analysis_results", [])
    user_query = state.get("user_query", "")

    numeric_cols = profile.get("numeric_columns", [])
    cat_cols = profile.get("categorical_columns", [])

    events = list(state.get("events", []))
    events.append({
        "stage": "Generate Visualizations",
        "agent": "Visualization Agent",
        "message": "Selecting optimal chart types and generating interactive Plotly specifications...",
        "timestamp": time.time(),
    })

    # Load dataframe for fallback or execution
    try:
        if file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
    except Exception:
        df = pd.DataFrame()

    visualizations: List[Dict[str, Any]] = []
    repl = PythonReplTool()

    # Prompt LLM for 2 custom visualization scripts tailored to the user's specific request
    viz_tasks = [
        {"type": "distribution_or_scatter", "focus": "Primary metric relationships or distribution"},
        {"type": "segmentation_or_comparison", "focus": "Segment comparison, cohort breakdown or trend"},
    ]

    for idx, task in enumerate(viz_tasks):
        prompt = f"""
Dataset Details:
{profile_summary}

User Query:
{user_query}

Visualization Objective:
Create an informative, high-impact Plotly visualization focusing on: {task['focus']}.
Remember to assign the figure to the variable `fig` (e.g. `fig = px.bar(...)` or `fig = px.scatter(...)`).
"""
        chart_obj = None
        try:
            llm = get_llm(temperature=0.2)
            resp = llm.invoke([
                SystemMessage(content=VIZ_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            code = resp.content.strip()
            match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", code)
            if match:
                code = match.group(1).strip()

            exec_res = repl.execute(code, file_path)
            if exec_res.success and exec_res.figure_json:
                fig_dict = json.loads(exec_res.figure_json)
                layout_title = fig_dict.get("layout", {}).get("title", {}).get("text", f"Visualization {idx+1}")
                chart_obj = {
                    "id": f"viz_custom_{idx+1}",
                    "title": str(layout_title),
                    "chart_type": task["type"],
                    "description": f"Interactive visualization targeting {task['focus']}.",
                    "figure": fig_dict,
                }
        except Exception as e:
            print(f"[Visualization Agent] Error generating custom chart {idx+1}: {e}")

        if chart_obj:
            visualizations.append(chart_obj)

    # If LLM didn't produce enough charts, enrich with deterministic fallback charts
    fallback_charts = _generate_fallback_charts(df, numeric_cols, cat_cols)
    existing_types = {v.get("chart_type") for v in visualizations}
    for fb in fallback_charts:
        if len(visualizations) < 3 and fb["chart_type"] not in existing_types:
            visualizations.append(fb)

    events.append({
        "stage": "Generate Visualizations",
        "agent": "Visualization Agent",
        "message": f"Successfully synthesized {len(visualizations)} interactive Plotly charts.",
        "timestamp": time.time(),
        "details": {"chart_titles": [v["title"] for v in visualizations]},
    })

    return {
        "visualizations": visualizations,
        "events": events,
    }

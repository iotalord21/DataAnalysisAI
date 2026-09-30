import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.agents.llm_factory import get_llm
from app.tools.python_repl import PythonReplTool
from app.tools.data_profiler import DataProfiler


CHAT_SYSTEM_PROMPT = """You are an expert Principal Data Scientist and Interactive Analytical Assistant.
The user is inspecting an active dataset and is asking a specific follow-up question or requesting an ad-hoc calculation.

You have access to the dataset pre-loaded in an isolated Python sandbox as the pandas DataFrame `df`.

Guidelines:
1. Whenever the user's question requires calculating numbers, aggregates, distributions, hypothesis tests, or filtering, write executable Python code to compute the exact answer.
2. If the user asks for a chart or visualization, write code using `plotly.express as px` or `plotly.graph_objects as go`, and assign the figure to the variable `fig`.
3. Assign summary metrics or computed tables to the variable `result` (e.g. `result = {"average": 45.2, "t_stat": 2.14}`).
4. Also use `print()` statements to print formatted summaries of the calculations.
5. In your code block, DO NOT import os, sys, subprocess, requests, or builtins (forbidden for sandbox isolation).
6. Format any code in a ```python ``` block.
"""

CHAT_RESPONSE_SYNTHESIS_PROMPT = """You are an expert Data Analyst presenting the results of a computed follow-up query.
Summarize the findings clearly, professionally, and concisely in GitHub-flavored Markdown.

Requirements:
- Directly answer the user's question using the exact numerical values computed.
- Cite specific figures, percentages, and metrics.
- Keep the response clear, structured, and actionable.
"""


def process_chat_query(
    file_path: str,
    user_query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    profile_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a conversational follow-up query:
    1. Formulates Python code to answer the query against `df`.
    2. Runs the code inside the PythonReplTool sandbox.
    3. Captures output data, tables, and optional Plotly figures.
    4. Synthesizes a verified, markdown response for the user.
    """
    conversation_history = conversation_history or []
    repl = PythonReplTool()

    # Step 1: Prompt LLM to write analysis / visualization code
    history_messages = []
    for msg in conversation_history[-6:]:
        if msg.get("role") == "user":
            history_messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            history_messages.append(AIMessage(content=msg.get("content", "")))

    prompt_content = f"""
Dataset Overview:
{profile_summary or 'Dataset is loaded as df.'}

User's Follow-Up Question:
{user_query}

Write Python code using `df` to calculate the answer. If a chart is requested or helpful, assign it to `fig`.
"""

    code_executed = ""
    stdout_output = ""
    result_data = None
    figure_json = None
    exec_success = True

    try:
        llm = get_llm(temperature=0.1)
        plan_resp = llm.invoke([
            SystemMessage(content=CHAT_SYSTEM_PROMPT),
            *history_messages,
            HumanMessage(content=prompt_content),
        ])
        raw_output = plan_resp.content.strip()

        # Extract python code
        match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", raw_output)
        if match:
            code_executed = match.group(1).strip()
            exec_res = repl.execute(code_executed, file_path)
            exec_success = exec_res.success
            stdout_output = exec_res.stdout
            result_data = exec_res.result_data

            if exec_res.figure_json:
                try:
                    figure_json = json.loads(exec_res.figure_json)
                except Exception:
                    figure_json = None

            if not exec_res.success:
                stdout_output += f"\n[Execution Note: {exec_res.error}]"

        # Step 2: Synthesize answer markdown
        synthesis_prompt = f"""
User Question:
{user_query}

Execution Code:
{code_executed}

Standard Output / Results:
{stdout_output}
Result Data: {result_data}

Please provide a clear, professional answer citing the computed numbers.
"""
        ans_resp = llm.invoke([
            SystemMessage(content=CHAT_RESPONSE_SYNTHESIS_PROMPT),
            HumanMessage(content=synthesis_prompt),
        ])
        final_answer = ans_resp.content.strip()

    except Exception as e:
        final_answer = f"I attempted to analyze your query, but encountered an error: {str(e)}."
        exec_success = False

    return {
        "answer": final_answer,
        "code_executed": code_executed if code_executed else None,
        "stdout": stdout_output if stdout_output else None,
        "figure": figure_json,
        "success": exec_success,
    }

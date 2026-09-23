"""
Subprocess entry point for executing user-generated data science code.
Loaded in an isolated process to protect memory, prevent state pollution, and enforce hard timeouts.
"""
import sys
import json
import traceback
from pathlib import Path
import pandas as pd
import numpy as np


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "Missing arguments to runner"}))
        sys.exit(1)

    dataset_path = sys.argv[1]
    code_path = sys.argv[2]

    # Pre-warmed context: load dataset
    try:
        p = Path(dataset_path)
        if p.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(p)
        else:
            df = pd.read_csv(p)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Failed to load dataset: {str(e)}"}))
        sys.exit(1)

    # Read user code
    try:
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Failed to read code file: {str(e)}"}))
        sys.exit(1)

    # Prepare execution environment
    import io
    from contextlib import redirect_stdout, redirect_stderr
    import plotly.graph_objects as go
    import plotly.express as px
    import scipy.stats as stats

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    # Safe restricted builtins
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
        "dict": dict, "dir": dir, "divmod": divmod, "enumerate": enumerate,
        "filter": filter, "float": float, "format": format, "frozenset": frozenset,
        "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
        "issubclass": issubclass, "iter": iter, "len": len, "list": list,
        "map": map, "max": max, "min": min, "next": next, "oct": oct,
        "ord": ord, "pow": pow, "print": print, "range": range, "repr": repr,
        "reversed": reversed, "round": round, "set": set, "slice": slice,
        "sorted": sorted, "str": str, "sum": sum, "tuple": tuple, "type": type,
        "zip": zip, "True": True, "False": False, "None": None,
    }

    env = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "pandas": pd,
        "np": np,
        "numpy": np,
        "px": px,
        "go": go,
        "stats": stats,
        "df": df,
        "result": None,
        "fig": None,
    }

    # Execute
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(code, env)

        result_val = env.get("result")
        fig_val = env.get("fig")

        # Serialize result if dataframe or series
        serialized_result = None
        if isinstance(result_val, pd.DataFrame):
            serialized_result = {
                "type": "dataframe",
                "columns": list(result_val.columns),
                "data": result_val.head(100).to_dict(orient="records"),
                "total_rows": len(result_val),
            }
        elif isinstance(result_val, pd.Series):
            serialized_result = {
                "type": "series",
                "name": str(result_val.name),
                "data": result_val.head(100).to_dict(),
            }
        elif result_val is not None:
            try:
                # Test json serializability
                json.dumps(result_val)
                serialized_result = {"type": "raw", "data": result_val}
            except (TypeError, OverflowError):
                serialized_result = {"type": "string", "data": str(result_val)}

        # Serialize figure if plotly
        figure_json = None
        if fig_val is not None:
            if hasattr(fig_val, "to_json"):
                figure_json = fig_val.to_json()
            elif isinstance(fig_val, dict):
                figure_json = json.dumps(fig_val)

        output = {
            "success": True,
            "stdout": stdout_buf.getvalue(),
            "stderr": stderr_buf.getvalue(),
            "result": serialized_result,
            "figure_json": figure_json,
        }
        print("__OUTPUT_START__")
        print(json.dumps(output))
        print("__OUTPUT_END__")

    except Exception as e:
        tb = traceback.format_exc()
        output = {
            "success": False,
            "error": str(e),
            "traceback": tb,
            "stdout": stdout_buf.getvalue(),
            "stderr": stderr_buf.getvalue(),
        }
        print("__OUTPUT_START__")
        print(json.dumps(output))
        print("__OUTPUT_END__")
        sys.exit(1)


if __name__ == "__main__":
    main()

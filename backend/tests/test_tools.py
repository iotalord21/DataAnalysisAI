import pytest
import pandas as pd
from app.tools.security import validate_python_code
from app.tools.python_repl import PythonReplTool
from app.tools.sql_runner import SqlRunnerTool
from app.tools.data_profiler import DataProfiler
from app.config import settings


def test_security_validation_allowed_code():
    code = """
import pandas as pd
import numpy as np
summary = df.describe()
result = {"mean": float(df['tenure'].mean())}
"""
    is_safe, error = validate_python_code(code)
    assert is_safe is True
    assert error is None


def test_security_validation_blocked_os_import():
    code = """
import os
os.system("rmdir /s /q test")
"""
    is_safe, error = validate_python_code(code)
    assert is_safe is False
    assert "restricted" in error.lower()


def test_security_validation_blocked_eval():
    code = """
eval("1 + 1")
"""
    is_safe, error = validate_python_code(code)
    assert is_safe is False
    assert "prohibited" in error.lower()


def test_data_profiler():
    df = pd.DataFrame({
        "age": [20, 25, 30, 35, 100],  # 100 is outlier
        "city": ["NY", "SF", "NY", "LA", "SF"],
    })
    profiler = DataProfiler()
    profile = profiler.profile_dataframe(df)

    assert profile["total_rows"] == 5
    assert profile["total_columns"] == 2
    assert "age" in profile["numeric_columns"]
    assert "city" in profile["categorical_columns"]
    assert profile["columns"]["age"]["outliers_count"] >= 1


def test_python_repl_execution():
    sample_file = settings.sample_data_dir / "customer_churn.csv"
    assert sample_file.exists()

    repl = PythonReplTool(timeout_seconds=10)
    code = """
mean_tenure = float(df['tenure'].mean())
print(f"Computed mean tenure: {mean_tenure}")
result = {"mean_tenure": round(mean_tenure, 2)}
"""
    exec_res = repl.execute(code, str(sample_file))
    assert exec_res.success is True
    assert "Computed mean tenure" in exec_res.stdout
    assert exec_res.result_data["data"]["mean_tenure"] > 0


def test_sql_runner_read_only():
    sample_file = settings.sample_data_dir / "customer_churn.csv"
    sql_runner = SqlRunnerTool()

    query = "SELECT gender, COUNT(*) as cnt, AVG(MonthlyCharges) as avg_mc FROM dataset GROUP BY gender"
    res = sql_runner.execute(query, str(sample_file))
    assert res.success is True
    assert len(res.rows) == 2
    assert "gender" in res.columns


def test_sql_runner_blocks_mutation():
    sample_file = settings.sample_data_dir / "customer_churn.csv"
    sql_runner = SqlRunnerTool()

    query = "DROP TABLE dataset;"
    res = sql_runner.execute(query, str(sample_file))
    assert res.success is False
    assert "disallowed" in res.error.lower()

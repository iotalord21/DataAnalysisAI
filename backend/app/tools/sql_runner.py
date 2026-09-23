import re
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel
import duckdb
import pandas as pd


class SqlExecutionResult(BaseModel):
    success: bool
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    query_executed: str = ""


# Disallowed keywords for read-only security
FORBIDDEN_SQL_KEYWORDS = {
    "ATTACH", "DETACH", "COPY", "EXPORT", "INSTALL", "LOAD",
    "PRAGMA", "DROP", "INSERT", "DELETE", "UPDATE", "ALTER",
    "CREATE", "REPLACE", "GRANT", "REVOKE", "VACUUM", "CALL"
}


class SqlRunnerTool:
    """
    In-memory DuckDB query runner for rapid analytics over CSV and Excel files.
    Enforces read-only SELECT/WITH queries.
    """

    def validate_query(self, query: str) -> Optional[str]:
        # Strip comments
        cleaned = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL).strip()

        tokens = re.findall(r"\b[A-Za-z]+\b", cleaned)
        for token in tokens:
            if token.upper() in FORBIDDEN_SQL_KEYWORDS:
                return f"Disallowed SQL keyword: '{token.upper()}'. Only read-only queries (SELECT/WITH) are permitted."

        first_word = tokens[0].upper() if tokens else ""
        if first_word not in ("SELECT", "WITH", "DESCRIBE", "EXPLAIN"):
            return "Query must start with SELECT, WITH, or DESCRIBE."

        return None

    def execute(self, query: str, dataset_path: str, limit: int = 500) -> SqlExecutionResult:
        start_time = time.time()

        # Step 1: Query security validation
        validation_error = self.validate_query(query)
        if validation_error:
            return SqlExecutionResult(
                success=False,
                error=validation_error,
                query_executed=query,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        # Step 2: Ensure file exists
        p = Path(dataset_path)
        if not p.exists():
            return SqlExecutionResult(
                success=False,
                error=f"Dataset not found at {dataset_path}",
                query_executed=query,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        con = duckdb.connect(database=":memory:")
        try:
            # Register file as 'dataset' and 'df'
            if p.suffix.lower() in [".xlsx", ".xls"]:
                # Load Excel via pandas then register in duckdb
                df_temp = pd.read_excel(p)
                con.register("dataset", df_temp)
                con.register("df", df_temp)
            else:
                escaped_path = str(p.resolve()).replace("\\", "/")
                con.execute(f"CREATE VIEW dataset AS SELECT * FROM read_csv_auto('{escaped_path}');")
                con.execute("CREATE VIEW df AS SELECT * FROM dataset;")

            # Execute query
            cursor = con.execute(query)
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            fetched_rows = cursor.fetchmany(limit)

            rows_dicts = [dict(zip(col_names, row)) for row in fetched_rows]
            execution_time_ms = round((time.time() - start_time) * 1000, 2)

            return SqlExecutionResult(
                success=True,
                columns=col_names,
                rows=rows_dicts,
                row_count=len(rows_dicts),
                query_executed=query,
                execution_time_ms=execution_time_ms,
            )
        except Exception as e:
            return SqlExecutionResult(
                success=False,
                error=str(e),
                query_executed=query,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        finally:
            con.close()

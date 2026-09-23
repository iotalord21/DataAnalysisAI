import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

from app.tools.security import validate_python_code
from app.config import settings


class ExecutionResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    result_data: Optional[Any] = None
    figure_json: Optional[str] = None
    execution_time_ms: float = 0.0
    code_executed: str = ""


class PythonReplTool:
    """
    Isolated Python Execution Environment with AST security auditing and subprocess sandboxing.
    Pre-warms the environment with the target dataset as `df`.
    """

    def __init__(self, timeout_seconds: Optional[int] = None):
        self.timeout_seconds = timeout_seconds or settings.execution_timeout_seconds
        self.runner_script = Path(__file__).resolve().parent / "runner_script.py"

    def execute(self, code: str, dataset_path: str) -> ExecutionResult:
        start_time = time.time()

        # Step 1: Security Audit via AST
        is_safe, violation = validate_python_code(code)
        if not is_safe:
            return ExecutionResult(
                success=False,
                error=f"Security Violation: {violation}",
                code_executed=code,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        # Step 2: Ensure dataset exists
        if not os.path.exists(dataset_path):
            return ExecutionResult(
                success=False,
                error=f"Dataset file not found at: {dataset_path}",
                code_executed=code,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        # Step 3: Write code to temporary script
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp_code_file:
            tmp_code_file.write(code)
            tmp_code_path = tmp_code_file.name

        try:
            # Step 4: Execute in isolated subprocess using the current Python environment
            cmd = [
                sys.executable,
                str(self.runner_script),
                str(dataset_path),
                tmp_code_path,
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            stdout = process.stdout
            stderr = process.stderr

            # Parse structured output between __OUTPUT_START__ and __OUTPUT_END__
            if "__OUTPUT_START__" in stdout and "__OUTPUT_END__" in stdout:
                payload = stdout.split("__OUTPUT_START__")[1].split("__OUTPUT_END__")[0].strip()
                parsed = json.loads(payload)
                return ExecutionResult(
                    success=parsed.get("success", False),
                    stdout=parsed.get("stdout", ""),
                    stderr=parsed.get("stderr", ""),
                    error=parsed.get("error"),
                    result_data=parsed.get("result"),
                    figure_json=parsed.get("figure_json"),
                    execution_time_ms=execution_time_ms,
                    code_executed=code,
                )
            else:
                # Subprocess exited without structured payload (e.g. fatal exit or crash)
                return ExecutionResult(
                    success=process.returncode == 0,
                    stdout=stdout,
                    stderr=stderr,
                    error=stderr if process.returncode != 0 else None,
                    execution_time_ms=execution_time_ms,
                    code_executed=code,
                )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error=f"Execution timed out after {self.timeout_seconds} seconds. Please optimize your calculations.",
                code_executed=code,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Subprocess execution error: {str(e)}",
                code_executed=code,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        finally:
            # Clean up temp file
            if os.path.exists(tmp_code_path):
                try:
                    os.remove(tmp_code_path)
                except OSError:
                    pass

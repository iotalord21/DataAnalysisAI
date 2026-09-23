import ast
from typing import Tuple, Optional, Set

# Whitelist of allowed modules for data science and analytics
ALLOWED_MODULES: Set[str] = {
    "pandas", "pd",
    "numpy", "np",
    "scipy", "stats",
    "statsmodels", "sm",
    "sklearn",
    "duckdb",
    "plotly", "px", "go",
    "math",
    "json",
    "datetime", "date", "time",
    "re",
    "collections",
    "itertools",
    "tabulate",
}

# Forbidden builtin and attribute calls that could break sandbox isolation
FORBIDDEN_CALLS: Set[str] = {
    "eval", "exec", "open", "compile", "__import__",
    "globals", "locals", "getattr", "setattr", "delattr",
    "exit", "quit", "breakpoint", "help", "input",
}

FORBIDDEN_MODULES: Set[str] = {
    "os", "sys", "subprocess", "shutil", "pty", "socket", "urllib",
    "requests", "http", "ftplib", "smtplib", "telnetlib", "xmlrpc",
    "multiprocessing", "threading", "asyncio", "ctypes", "builtins",
    "importlib", "pip", "site", "inspect", "platform", "signal",
}


class CodeSecurityValidator(ast.NodeVisitor):
    def __init__(self):
        self.is_safe = True
        self.violation: Optional[str] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            root_mod = alias.name.split(".")[0]
            if root_mod in FORBIDDEN_MODULES or root_mod not in ALLOWED_MODULES:
                self.is_safe = False
                self.violation = f"Import of module '{alias.name}' is restricted for security."
                return
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            root_mod = node.module.split(".")[0]
            if root_mod in FORBIDDEN_MODULES or root_mod not in ALLOWED_MODULES:
                self.is_safe = False
                self.violation = f"Import from module '{node.module}' is restricted for security."
                return
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Disallow dangerous builtins directly
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                self.is_safe = False
                self.violation = f"Call to '{node.func.id}()' is prohibited for sandbox security."
                return

        # Check for dynamic attribute calls or dunder access
        if isinstance(node.func, ast.Attribute):
            if node.func.attr.startswith("__") and node.func.attr.endswith("__"):
                self.is_safe = False
                self.violation = f"Access to dunder attribute/method '{node.func.attr}' is prohibited."
                return

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Disallow dunder attributes like __subclasses__, __globals__, __dict__
        if node.attr.startswith("__") and node.attr.endswith("__"):
            self.is_safe = False
            self.violation = f"Direct access to dunder attribute '{node.attr}' is prohibited."
            return
        self.generic_visit(node)


def validate_python_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validates Python code using AST parsing against sandbox security rules.
    Returns (is_safe, error_message).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error in generated code: {e.msg} at line {e.lineno}"

    validator = CodeSecurityValidator()
    validator.visit(tree)

    return validator.is_safe, validator.violation

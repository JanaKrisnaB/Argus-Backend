"""
core/tools.py — Static analysis tools (zero LLM API calls).
"""
import ast
import json
import os
import subprocess
import tempfile

from langchain_core.tools import tool
from radon.complexity import cc_rank, cc_visit


@tool
def flake8_tool(code: str) -> str:
    """Runs flake8 linter on Python code. Returns violations as JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["flake8", "--format=%(row)d::%(col)d::%(code)s::%(text)s", tmp_path],
            capture_output=True, text=True,
        )
        violations = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("::")
            if len(parts) == 4:
                violations.append({
                    "line": int(parts[0].split(":")[-1]),
                    "col": int(parts[1]),
                    "code": parts[2],
                    "message": parts[3],
                })
        return json.dumps(violations)
    finally:
        os.unlink(tmp_path)


@tool
def radon_tool(code: str) -> str:
    """Analyzes cyclomatic complexity. Returns per-function scores as JSON."""
    try:
        return json.dumps([
            {
                "name": b.name,
                "line": b.lineno,
                "complexity": b.complexity,
                "rank": cc_rank(b.complexity),
                "is_high_risk": b.complexity > 5,
            }
            for b in cc_visit(code)
        ])
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@tool
def ast_tool(code: str) -> str:
    """Parses Python AST. Returns functions, classes, imports as JSON."""
    try:
        tree = ast.parse(code)
        functions, classes, imports = [], [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [a.arg for a in node.args.args],
                    "has_docstring": ast.get_docstring(node) is not None,
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": ast.get_docstring(node) is not None,
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    f"from {node.module} import {', '.join(a.name for a in node.names)}"
                )
        return json.dumps({"functions": functions, "classes": classes, "imports": imports})
    except SyntaxError as exc:
        return json.dumps({"error": str(exc)})


TOOLS = [flake8_tool, radon_tool, ast_tool]

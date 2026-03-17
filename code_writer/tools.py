"""
MCP Tool Server for Code Writer Agent
Run standalone: python tools.py
"""
import ast
import re
import textwrap
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Code Writer Tools")


@mcp.tool()
def validate_python_syntax(source_code: str) -> str:
    """
    Validate Python syntax and return either 'Valid Python syntax.'
    or a detailed error describing the problem.
    """
    try:
        ast.parse(source_code)
        return "Valid Python syntax."
    except SyntaxError as e:
        return (
            f"SyntaxError — line {e.lineno}, col {e.offset}: {e.msg}\n"
            f"Offending text: {e.text!r}"
        )


@mcp.tool()
def format_code_block(code: str, language: str = "python") -> str:
    """
    Wrap a code snippet in a fenced Markdown code block for clean display.
    Optionally dedents the code to remove unnecessary leading whitespace.
    """
    clean = textwrap.dedent(code).strip()
    return f"```{language}\n{clean}\n```"


@mcp.tool()
def extract_imports(source_code: str) -> str:
    """
    Parse Python source and return all import statements found,
    one per line. Useful for producing a requirements list.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return f"Cannot parse source: {e}"

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            imports.append(f"from {module} import {names}")

    if not imports:
        return "No import statements found."
    return "\n".join(sorted(set(imports)))


@mcp.tool()
def generate_docstring_template(
    function_name: str,
    params: str,
    return_type: str = "None",
    description: str = "",
) -> str:
    """
    Generate a Google-style docstring template for a function.

    Args:
        function_name: Name of the function.
        params: Comma-separated parameter names, e.g. 'name, age, city'.
        return_type: Return type annotation string, e.g. 'str', 'int', 'None'.
        description: One-line description of what the function does.
    """
    param_list = [p.strip() for p in params.split(",") if p.strip()]
    desc_line = description or f"TODO: describe what {function_name} does."

    lines = [
        f'def {function_name}({", ".join(param_list)}) -> {return_type}:',
        f'    """',
        f'    {desc_line}',
        "",
    ]

    if param_list:
        lines.append("    Args:")
        for p in param_list:
            lines.append(f"        {p}: TODO — describe this parameter.")

    if return_type != "None":
        lines.append("")
        lines.append("    Returns:")
        lines.append(f"        {return_type}: TODO — describe the return value.")

    lines.append('    """')
    lines.append("    pass")

    return "\n".join(lines)


@mcp.tool()
def list_functions_and_classes(source_code: str) -> str:
    """
    Return the names of all top-level functions and classes defined
    in the given Python source code.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return f"Cannot parse source: {e}"

    functions = []
    classes = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    parts = []
    if classes:
        parts.append("Classes:\n" + "\n".join(f"  • {c}" for c in classes))
    if functions:
        parts.append("Functions:\n" + "\n".join(f"  • {f}" for f in functions))
    if not parts:
        return "No top-level functions or classes found."
    return "\n\n".join(parts)


@mcp.tool()
def add_type_hints_reminder(source_code: str) -> str:
    """
    Scan function definitions and flag any that are missing type hints
    on parameters or return type. Returns a list of warnings.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return f"Cannot parse source: {e}"

    warnings = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            missing = []
            for arg in node.args.args:
                if arg.annotation is None and arg.arg != "self":
                    missing.append(arg.arg)
            if missing:
                warnings.append(
                    f"  `{node.name}` — missing type hints on: {', '.join(missing)}"
                )
            if node.returns is None:
                warnings.append(
                    f"  `{node.name}` — missing return type annotation (-> ...)"
                )

    if not warnings:
        return "All functions have type hints. ✓"
    return "Functions missing type hints:\n" + "\n".join(warnings)


if __name__ == "__main__":
    mcp.run()
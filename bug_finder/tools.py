"""
MCP Tool Server for Bug Finder Agent
Run standalone: python tools.py
"""
import ast
import traceback as tb_module
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Bug Finder Tools")


@mcp.tool()
def analyze_traceback(traceback: str) -> str:
    """
    Parse a Python traceback string and return a structured summary:
    error type, message, file + line of the crash, and the immediate
    call-chain frames.
    """
    lines = traceback.strip().splitlines()
    error_type = "Unknown"
    error_message = ""
    frames = []

    for i, line in enumerate(lines):
        # Capture "File ..., line N, in ..."
        match = re.match(r'\s*File "(.+)", line (\d+), in (.+)', line)
        if match:
            frames.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "scope": match.group(3),
            })
        # Last non-empty line is usually "ErrorType: message"
        if i == len(lines) - 1 and line.strip():
            parts = line.split(":", 1)
            error_type = parts[0].strip()
            error_message = parts[1].strip() if len(parts) > 1 else ""

    if not frames:
        return f"Could not parse traceback.\nRaw input:\n{traceback}"

    crash_frame = frames[-1]
    summary_lines = [
        f"Error Type   : {error_type}",
        f"Message      : {error_message}",
        f"Crash Site   : {crash_frame['file']} — line {crash_frame['line']} in `{crash_frame['scope']}`",
        "",
        "Call Chain (oldest → newest):",
    ]
    for idx, f in enumerate(frames, 1):
        summary_lines.append(
            f"  {idx}. {f['file']}:{f['line']} in `{f['scope']}`"
        )

    return "\n".join(summary_lines)


@mcp.tool()
def check_syntax(source_code: str, filename: str = "<string>") -> str:
    """
    Check Python source code for syntax errors using the AST parser.
    Returns 'No syntax errors found.' or a detailed error message.
    """
    try:
        ast.parse(source_code, filename=filename)
        return "No syntax errors found."
    except SyntaxError as e:
        return (
            f"SyntaxError at line {e.lineno}, column {e.offset}:\n"
            f"  {e.msg}\n"
            f"  Offending text: {e.text!r}"
        )


@mcp.tool()
def identify_common_error(error_type: str, error_message: str) -> str:
    """
    Given an error type and message, return a plain-English explanation
    and a typical fix strategy.
    """
    error_type = error_type.strip()
    error_message = error_message.strip().lower()

    patterns = {
        "NameError": (
            "A variable or function name was used before it was defined or imported.",
            "Fix: Check spelling, make sure the variable is assigned before use, "
            "or add the missing import."
        ),
        "TypeError": (
            "An operation was applied to a value of the wrong type.",
            "Fix: Check function argument types, use str()/int()/float() to convert, "
            "or inspect what the function actually returns."
        ),
        "AttributeError": (
            "An attribute or method does not exist on that object.",
            "Fix: Verify the object type with type(), check for None values, "
            "and consult the class/module docs for the correct attribute name."
        ),
        "IndexError": (
            "A sequence was accessed with an index that is out of range.",
            "Fix: Check list/tuple length before indexing; use len() guard or try/except."
        ),
        "KeyError": (
            "A dictionary was accessed with a key that does not exist.",
            "Fix: Use dict.get(key, default), check 'key in dict' first, "
            "or print dict.keys() to see what's available."
        ),
        "ImportError": (
            "A module could not be imported.",
            "Fix: Run 'pip install <package>', check the module name spelling, "
            "or verify your PYTHONPATH / virtual-env is active."
        ),
        "ModuleNotFoundError": (
            "The module does not exist in the current environment.",
            "Fix: Install via pip, check the package name, or confirm the file path."
        ),
        "ValueError": (
            "A function received an argument of the right type but an invalid value.",
            "Fix: Validate input before passing it, handle edge cases (empty strings, "
            "negative numbers, etc.)."
        ),
        "ZeroDivisionError": (
            "Division (or modulo) by zero was attempted.",
            "Fix: Guard with 'if divisor != 0' before dividing."
        ),
        "FileNotFoundError": (
            "The specified file or directory does not exist.",
            "Fix: Check the path string (absolute vs relative), verify the file exists "
            "with os.path.exists(), or handle the error with try/except."
        ),
        "RecursionError": (
            "The maximum recursion depth was exceeded.",
            "Fix: Add a proper base case to your recursive function, "
            "or refactor to an iterative approach."
        ),
        "StopIteration": (
            "next() was called on an exhausted iterator.",
            "Fix: Wrap in a try/except StopIteration, or use a for loop instead."
        ),
    }

    if error_type in patterns:
        explanation, fix = patterns[error_type]
        return f"**{error_type}**\n\nWhat it means: {explanation}\n\n{fix}"

    # Fallback: keyword scan on message
    if "none" in error_message or "nonetype" in error_message:
        return (
            "Looks like a NoneType error.\n"
            "A variable that was expected to hold an object contains None instead.\n"
            "Fix: Trace back where the value is set; add a None-check before use."
        )
    if "connection" in error_message or "timeout" in error_message:
        return (
            "Looks like a network/connection error.\n"
            "Fix: Verify the server is running, check the host/port, "
            "increase the timeout, and handle retries."
        )

    return (
        f"No specific pattern matched for '{error_type}'.\n"
        "Suggestion: search the full error message online, check the stack trace "
        "for the exact line that raised the error, and add print/logging statements "
        "around that area."
    )


@mcp.tool()
def suggest_fix(code_snippet: str, error_description: str) -> str:
    """
    Given a short code snippet and an error description, return focused
    fix suggestions (static heuristics — no execution).
    """
    suggestions = []

    # Undefined name heuristic
    undef = re.search(r"name '(\w+)' is not defined", error_description)
    if undef:
        name = undef.group(1)
        suggestions.append(
            f"• '{name}' is not defined. Ensure it is imported or assigned before use.\n"
            f"  Quick check: grep for 'import {name}' or '{name} =' above this line."
        )

    # Missing comma / bracket heuristic
    if "SyntaxError" in error_description:
        suggestions.append(
            "• SyntaxError detected. Common causes:\n"
            "  – Missing colon after if/for/def/class\n"
            "  – Unclosed parenthesis, bracket, or quote\n"
            "  – Invalid indentation (mix of tabs and spaces)\n"
            "  Tip: Run `python -m py_compile <file>` for a quick check."
        )

    # await outside async
    if "await" in code_snippet and "async def" not in code_snippet:
        suggestions.append(
            "• 'await' is used but the function is not declared 'async def'.\n"
            "  Fix: Change 'def' to 'async def' in the enclosing function."
        )

    # Bare except
    if re.search(r"except\s*:", code_snippet):
        suggestions.append(
            "• Bare 'except:' found. This silences ALL exceptions, making debugging hard.\n"
            "  Fix: Replace with 'except Exception as e:' and log 'e'."
        )

    # print as statement (Python 2 vs 3)
    if re.search(r"^\s*print\s+[\"']", code_snippet, re.MULTILINE):
        suggestions.append(
            "• Looks like Python 2 print statement syntax.\n"
            "  Fix: Use print(...) with parentheses."
        )

    if not suggestions:
        suggestions.append(
            "No automated heuristic matched. Recommended steps:\n"
            "1. Read the full traceback top-to-bottom.\n"
            "2. Identify the file + line number of the crash.\n"
            "3. Add a print/logging statement just before that line.\n"
            "4. Verify the types/values of all variables involved."
        )

    return "\n\n".join(suggestions)


if __name__ == "__main__":
    mcp.run()
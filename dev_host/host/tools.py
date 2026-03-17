"""
MCP Tool Server for Dev Host Agent
Run standalone: python tools.py

The host agent uses these tools to parse user requests before deciding
which client agent to call (bug_finder or code_writer).
"""
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Dev Host Tools")


@mcp.tool()
def classify_request(user_message: str) -> str:
    """
    Classify a user message as 'bug_finder', 'code_writer', or 'both'.
    Returns a JSON-like string with the decision and reasoning.

    Args:
        user_message: The raw message from the end user.
    """
    msg = user_message.lower()

    bug_keywords = [
        "error", "traceback", "crash", "exception", "bug", "fix",
        "broken", "fails", "failure", "stacktrace", "stack trace",
        "not working", "unexpected", "debug", "why does",
    ]
    code_keywords = [
        "write", "create", "generate", "implement", "make a", "build",
        "snippet", "example", "how to", "code for", "script", "function",
        "class", "module", "template",
    ]

    has_bug   = any(kw in msg for kw in bug_keywords)
    has_code  = any(kw in msg for kw in code_keywords)

    if has_bug and has_code:
        decision = "both"
        reason   = "Request mentions both an error/bug AND a code-writing task."
    elif has_bug:
        decision = "bug_finder"
        reason   = "Request describes an error, crash, or debugging need."
    elif has_code:
        decision = "code_writer"
        reason   = "Request asks for code to be written or generated."
    else:
        decision = "code_writer"
        reason   = "No strong signal detected; defaulting to code_writer."

    return (
        f"decision: {decision}\n"
        f"reason  : {reason}"
    )


@mcp.tool()
def extract_code_and_error(user_message: str) -> str:
    """
    Extract any code block (```...```) and error text from a user message.
    Returns the extracted pieces so the host can forward them to the
    correct client agent cleanly.

    Args:
        user_message: Raw message that may contain fenced code blocks
                      and/or a traceback.
    """
    # Pull fenced code blocks
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", user_message, re.DOTALL)

    # Pull traceback-like sections
    traceback_pattern = re.compile(
        r"(Traceback \(most recent call last\).*?)(?:\n\n|\Z)", re.DOTALL
    )
    tracebacks = traceback_pattern.findall(user_message)

    parts = []
    if code_blocks:
        for i, block in enumerate(code_blocks, 1):
            parts.append(f"[Code Block {i}]\n{block.strip()}")
    if tracebacks:
        for i, tb in enumerate(tracebacks, 1):
            parts.append(f"[Traceback {i}]\n{tb.strip()}")

    if not parts:
        return "No code blocks or tracebacks found in the message."
    return "\n\n---\n\n".join(parts)


@mcp.tool()
def build_agent_prompt(
    agent_name: str,
    original_request: str,
    extracted_code: str = "",
    extracted_error: str = "",
) -> str:
    """
    Build a clean, focused prompt to send to a client agent.

    Args:
        agent_name      : 'bug_finder' or 'code_writer'
        original_request: The user's original message.
        extracted_code  : Optional code snippet already parsed out.
        extracted_error : Optional traceback/error already parsed out.
    """
    if agent_name == "bug_finder":
        header = "You are receiving a bug-finding task. Analyze the following:"
    else:
        header = "You are receiving a code-writing task. Complete the following:"

    lines = [header, ""]
    lines.append(f"User Request:\n{original_request.strip()}")

    if extracted_code:
        lines.append(f"\nCode Snippet:\n```\n{extracted_code.strip()}\n```")
    if extracted_error:
        lines.append(f"\nError / Traceback:\n{extracted_error.strip()}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
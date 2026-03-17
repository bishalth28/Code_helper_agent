# 🤖 Code Helper — Multi-Agent AI System

A multi-agent AI system built with **Google ADK**, **A2A protocol**, and **MCP (Model Context Protocol)** that helps developers write code and debug errors. A central orchestrator agent intelligently routes requests to two specialist sub-agents — a **Bug Finder** and a **Code Writer** — each powered by their own tool server.

---

## 📌 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Agents](#agents)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Running the System](#running-the-system)
- [How It Works](#how-it-works)
- [MCP Tools Reference](#mcp-tools-reference)
- [Configuration](#configuration)
- [Security Notice](#security-notice)

---

## Architecture Overview

```
                        ┌─────────────────────────────┐
                        │         Dev Host             │
                        │  (Google ADK Orchestrator)   │
                        │   OpenRouter / LiteLLM       │
                        └──────────┬──────────┬────────┘
                                   │  A2A      │  A2A
                     ┌─────────────▼──┐   ┌───▼─────────────┐
                     │   Bug Finder   │   │   Code Writer   │
                     │  port :10004   │   │  port :10005    │
                     │  (A2A Agent)   │   │  (A2A Agent)    │
                     └───────┬────────┘   └──────┬──────────┘
                             │ MCP                │ MCP
                     ┌───────▼────────┐   ┌──────▼──────────┐
                     │  bug_finder/   │   │  code_writer/   │
                     │   tools.py     │   │   tools.py      │
                     └────────────────┘   └─────────────────┘
```

The **Dev Host** receives user messages, classifies the intent, and delegates to one or both specialist agents over the **A2A (Agent-to-Agent)** protocol. Each specialist agent uses its own **MCP tool server** to perform structured analysis.

---

## Agents

### 🔍 Bug Finder (`bug_finder/`) — Port 10004
Receives a code snippet or traceback and returns a structured bug analysis with concrete fix suggestions.

**MCP Tools:**
| Tool | Description |
|------|-------------|
| `analyze_traceback` | Parses a Python traceback into error type, message, crash site, and call chain |
| `check_syntax` | Validates Python source code using the AST parser |
| `identify_common_error` | Maps well-known error types (NameError, TypeError, etc.) to plain-English explanations and fix strategies |
| `suggest_fix` | Applies static heuristics to a code snippet and error description to generate targeted fix hints |

---

### ✍️ Code Writer (`code_writer/`) — Port 10005
Receives a natural-language prompt and returns a clean, minimal, working code snippet with a brief explanation.

**MCP Tools:**
| Tool | Description |
|------|-------------|
| `validate_python_syntax` | Checks generated code for syntax errors before returning it |
| `format_code_block` | Wraps code in a fenced Markdown block with optional language tagging |
| `extract_imports` | Parses source and lists all import statements (useful for generating requirements) |
| `generate_docstring_template` | Produces a Google-style docstring scaffold for a given function signature |
| `list_functions_and_classes` | Returns all top-level function and class names found in source code |
| `add_type_hints_reminder` | Scans function definitions and flags any missing type hint annotations |

---

### 🧠 Dev Host (`dev_host/`) — Orchestrator
The central orchestrator built with **Google ADK**. It reads the user's message, decides which specialist(s) to call, delegates via A2A, and returns a unified response.

**MCP Tools:**
| Tool | Description |
|------|-------------|
| `classify_request` | Classifies user intent as `bug_finder`, `code_writer`, or `both` using keyword heuristics |
| `extract_code_and_error` | Extracts fenced code blocks and traceback sections from a raw user message |
| `build_agent_prompt` | Constructs a clean, focused prompt to forward to a specialist agent |

---

## Project Structure

```
code_helper/
│
├── bug_finder/
│   ├── agent.py            # BugFinder class — wraps OpenRouter + MCP tool server
│   ├── agent_executor.py   # A2A AgentExecutor — handles task lifecycle
│   ├── tools.py            # MCP FastMCP tool server (runs standalone)
│   ├── __main__.py         # A2A server entry point (AgentCard + Uvicorn)
│   ├── main.py             # Basic entry point
│   └── pyproject.toml      # Dependencies (a2a-sdk, openai-agents, uvicorn)
│
├── code_writer/
│   ├── agent.py            # CodeWriter class — wraps OpenRouter + MCP tool server
│   ├── agent_executor.py   # A2A AgentExecutor — handles task lifecycle
│   ├── tools.py            # MCP FastMCP tool server (runs standalone)
│   ├── __main__.py         # A2A server entry point (AgentCard + Uvicorn)
│   ├── main.py             # Basic entry point
│   └── pyproject.toml      # Dependencies (a2a-sdk, openai-agents, uvicorn)
│
└── dev_host/
    ├── host/
    │   ├── agent.py        # DevHost class — Google ADK orchestrator + A2A clients
    │   ├── tools.py        # MCP FastMCP tool server for request routing
    │   └── .env            # Environment variables (API keys)
    ├── main.py             # Basic entry point
    └── pyproject.toml      # Dependencies (google-adk, litellm, a2a-sdk, httpx)
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Orchestration | [Google ADK](https://google.github.io/adk-docs/) |
| Agent Communication | [A2A Protocol](https://github.com/google/a2a) (a2a-sdk) |
| Tool Protocol | [MCP](https://modelcontextprotocol.io/) via `fastmcp` |
| LLM Provider | [OpenRouter](https://openrouter.ai/) |
| LLM Model | `z-ai/glm-4.5-air:free` (via OpenAI-compatible API) |
| LLM Bridge | `LiteLLM` (for ADK ↔ OpenRouter) |
| HTTP Server | Uvicorn + Starlette |
| Language | Python 3.13+ |
| Package Manager | [uv](https://docs.astral.sh/uv/) |

---

## Getting Started

### Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed

### 1. Clone the repository

```bash
git clone https://github.com/your-username/code-helper.git
cd code-helper
```

### 2. Set up environment variables

Create a `.env` file inside `dev_host/host/`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 3. Install dependencies for each agent

Each sub-project uses `uv` with its own `pyproject.toml`:

```bash
# Bug Finder
cd bug_finder && uv sync && cd ..

# Code Writer
cd code_writer && uv sync && cd ..

# Dev Host
cd dev_host && uv sync && cd ..
```

---

## Running the System

All three services must be running simultaneously. Open **three separate terminals**:

### Terminal 1 — Start Bug Finder (port 10004)

```bash
cd bug_finder
uv run python __main__.py
```

Expected output:
```
INFO:     Uvicorn running on http://localhost:10004
```

### Terminal 2 — Start Code Writer (port 10005)

```bash
cd code_writer
uv run python __main__.py
```

Expected output:
```
INFO:     Uvicorn running on http://localhost:10005
```

### Terminal 3 — Start Dev Host (Google ADK)

```bash
cd dev_host
adk web
```

Then open the ADK web interface in your browser to interact with the **Dev Host** orchestrator.

---

## How It Works

### Request Routing

When the Dev Host receives a message, it follows this decision process:

```
User Message
     │
     ▼
classify_request()
     │
     ├── "bug_finder"  → Error/traceback/crash keyword detected
     │                   → Forward to Bug Finder agent
     │
     ├── "code_writer" → Code generation keyword detected
     │                   → Forward to Code Writer agent
     │
     └── "both"        → Both signals detected
                         → Call Bug Finder AND Code Writer
                         → Merge results into one response
```

### Example Interactions

**Bug Fixing:**
```
User: "My script keeps raising a KeyError on line 42. Here's the traceback: ..."
→ Dev Host classifies as: bug_finder
→ Forwards to Bug Finder agent on :10004
→ Bug Finder runs: analyze_traceback → identify_common_error → suggest_fix
→ Returns structured analysis with fix suggestions
```

**Code Generation:**
```
User: "Write a FastAPI endpoint that accepts a username and returns a greeting."
→ Dev Host classifies as: code_writer
→ Forwards to Code Writer agent on :10005
→ Code Writer runs: validate_python_syntax → format_code_block
→ Returns a clean, working code snippet with explanation
```

**Combined:**
```
User: "This function crashes with TypeError — fix it and rewrite it properly."
→ Dev Host classifies as: both
→ Calls Bug Finder for diagnosis, Code Writer for the rewrite
→ Returns combined: bug analysis + corrected code
```

---

## MCP Tools Reference

### Bug Finder Tools (`bug_finder/tools.py`)

#### `analyze_traceback(traceback: str) → str`
Parses a Python traceback and returns the error type, message, crash site (file + line + scope), and the full call chain from oldest to newest frame.

#### `check_syntax(source_code: str, filename: str) → str`
Uses Python's `ast.parse()` to detect syntax errors. Returns either `"No syntax errors found."` or a detailed error with line/column info.

#### `identify_common_error(error_type: str, error_message: str) → str`
Covers 12+ built-in Python exception types with plain-English explanations and actionable fix strategies. Falls back to keyword scanning for NoneType and network errors.

#### `suggest_fix(code_snippet: str, error_description: str) → str`
Static heuristic analysis covering undefined names, syntax issues, `await` outside `async def`, bare `except:` clauses, and Python 2 print syntax.

---

### Code Writer Tools (`code_writer/tools.py`)

#### `validate_python_syntax(source_code: str) → str`
AST-based syntax validation returning `"Valid Python syntax."` or a SyntaxError with line and column.

#### `format_code_block(code: str, language: str) → str`
Dedents and wraps code in a fenced Markdown block (default: `python`).

#### `extract_imports(source_code: str) → str`
Parses an AST and returns all `import` and `from ... import` statements, deduplicated and sorted.

#### `generate_docstring_template(function_name, params, return_type, description) → str`
Generates a Google-style docstring scaffold with `Args:` and `Returns:` sections.

#### `list_functions_and_classes(source_code: str) → str`
Returns all top-level `def`, `async def`, and `class` names defined in the source.

#### `add_type_hints_reminder(source_code: str) → str`
Walks all function definitions and flags parameters and return types missing annotations.

---

### Dev Host Tools (`dev_host/host/tools.py`)

#### `classify_request(user_message: str) → str`
Keyword-based classifier returning `bug_finder`, `code_writer`, or `both` with reasoning.

#### `extract_code_and_error(user_message: str) → str`
Regex-based extractor for fenced code blocks and Python tracebacks from raw user messages.

#### `build_agent_prompt(agent_name, original_request, extracted_code, extracted_error) → str`
Assembles a structured prompt to send to a specialist agent, bundling the original request with any extracted code or error text.

---

## Configuration

| Setting | Location | Description |
|---------|----------|-------------|
| `OPENROUTER_API_KEY` | `dev_host/host/.env` | Your OpenRouter API key |
| Bug Finder port | `bug_finder/__main__.py` | Default: `10004` |
| Code Writer port | `code_writer/__main__.py` | Default: `10005` |
| Remote agent URLs | `dev_host/host/agent.py` | Defaults: `localhost:10004`, `localhost:10005` |
| LLM Model | All `agent.py` files | Default: `z-ai/glm-4.5-air:free` |

To swap models, change the model string in each `agent.py` to any model supported by OpenRouter:

```python
model="openai/gpt-4o-mini"
model="anthropic/claude-3-haiku"
```

---

## Security Notice

> ⚠️ **API keys must never be hardcoded in source files.**

Move all secrets to environment variables before committing or sharing:

```python
# Instead of hardcoding:
OPENROUTER_API_KEY = "sk-or-v1-..."

# Use:
import os
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
```

Store the key in `dev_host/host/.env` and ensure `.env` is listed in `.gitignore`.

---

## Contributing

Some ideas for extending the system:

- Add a **Test Writer** agent that generates unit tests for a given function
- Add a **Code Reviewer** agent for style, security, and performance feedback
- Persist agent sessions with a real database (replacing `InMemoryTaskStore`)
- Add streaming support for long responses
- Build a web UI as an alternative to the ADK interface

import os
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = "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"
class BugFinder:

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.openrouter = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
        self.model = OpenAIChatCompletionsModel(
            model="z-ai/glm-4.5-air:free",
            openai_client=self.openrouter,
        )

    async def ask_agent(self, code: str) -> str:
        async with MCPServerStdio(
            name="Bug Finder Tools",
            params={"command": "python", "args": ["tools.py"]},
        ) as tool_server:
            agent = Agent(
                name="Bug Finder",
                instructions=(
                    "You are an expert bug finder. "
                    "Analyse the provided code or traceback, identify every bug, "
                    "and suggest concrete fixes. Use your tools where helpful."
                ),
                model=self.model,
                mcp_servers=[tool_server],
            )
            try:
                result = await Runner.run(agent, code)
                return result.final_output
            except Exception as e:
                print(f"[ERROR] bug_finder.ask_agent: {e}")
                return f"Sorry, I encountered an error: {e}"
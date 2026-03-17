import os
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI


e
OPENROUTER_API_KEY = "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"

class CodeWriter:

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

    async def ask_agent(self, prompt_text: str) -> str:
        async with MCPServerStdio(
            name="Code Writer Tools",
            params={"command": "python", "args": ["tools.py"]},
        ) as tool_server:
            agent = Agent(
                name="Code Writer",
                instructions=(
                    "You are an expert coding assistant. "
                    "Given a prompt, produce a clean, minimal, working code snippet. "
                    "Use your tools to validate syntax and format the output. "
                    "Always include a short explanation after the code."
                ),
                model=self.model,
                mcp_servers=[tool_server],
            )
            try:
                result = await Runner.run(agent, prompt_text)
                return result.final_output
            except Exception as e:
                print(f"[ERROR] code_writer.ask_agent: {e}")
                return f"Sorry, I encountered an error: {e}"
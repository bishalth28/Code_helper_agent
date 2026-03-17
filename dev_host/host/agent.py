"""
Dev Host Agent — orchestrates bug_finder (port 10004) and code_writer (port 10005).

Framework: Google ADK  (google-adk)
Model    : OpenRouter via LiteLlm (google.adk.models.lite_llm)
Clients  : bug_finder + code_writer via A2A protocol
"""

import asyncio
import os
import uuid

import httpx
import nest_asyncio
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm 
from google.adk.tools.tool_context import ToolContext

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
)

load_dotenv()
nest_asyncio.apply()


class RemoteAgentConnection:
    """Wraps a single A2A client connection to one remote agent."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        self.agent_card = agent_card
        self.agent_url = agent_url
        self.http_client = httpx.AsyncClient(timeout=120)
        self.client = A2AClient(self.http_client, agent_card, url=agent_url)

    async def send_message(self, request: SendMessageRequest) -> SendMessageResponse:
        return await self.client.send_message(request)


class DevHost:
    """
    Host agent for the Code Helper system.
    Uses Google ADK + OpenRouter (via LiteLlm) to orchestrate
    bug_finder and code_writer client agents over A2A.
    """

    def __init__(self, remote_agent_urls: list[str]):
        self.remote_agent_urls = remote_agent_urls or []
        self.remote_connections: dict[str, RemoteAgentConnection] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agent: Agent | None = None

    async def create_agent(self) -> Agent:
        await self._load_remote_agents()

        self.agent = Agent(
            model=LiteLlm(model="openrouter/z-ai/glm-4.5-air:free"),
            name="dev_host",
            description="Orchestrator for the Code Helper multi-agent system.",
            instruction=self._get_instruction(),
            tools=[self.send_message_to_agent],
        )
        return self.agent

    def _get_instruction(self) -> str:
        agents_list = "\n".join(
            f"  • {name}" for name in self.cards
        ) or "  (none connected)"

        return f"""
You are the **Dev Host** — the orchestrator of the Code Helper agent system.

Your job:
1. Read the user's message carefully.
2. Decide which specialist agent to call:
   - **Bug Finder**  → when there is an error, traceback, crash, or debugging request.
   - **Code Writer** → when the user wants code written or generated.
   - **both**        → when the request needs both debugging AND new code.
3. Call `send_message_to_agent` with the exact agent name and a clear task.
4. Collect the response(s) and return a single, well-formatted answer.

Connected agents:
{agents_list}

Rules:
- Never write code yourself — always delegate to the right specialist.
- If the user's intent is unclear, ask one clarifying question first.
- Always mention which agent produced each part of the answer.
"""

    async def _load_remote_agents(self) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            for url in self.remote_agent_urls:
                resolver = A2ACardResolver(client, url)
                card = await resolver.get_agent_card()
                self.remote_connections[card.name] = RemoteAgentConnection(card, url)
                self.cards[card.name] = card

    async def send_message_to_agent(
        self,
        agent_name: str,
        task: str,
        tool_context: ToolContext,
    ) -> str:
        """
        Send a task to a remote specialist agent and return its reply.

        Args:
            agent_name: Exact name of the agent — 'Bug Finder' or 'Code Writer'.
            task: The task description to forward to the agent.
            tool_context: Injected by Google ADK — do not pass manually.
        """
        connection = self.remote_connections.get(agent_name)
        if not connection:
            available = list(self.remote_connections.keys())
            return f"No agent named '{agent_name}'. Available agents: {available}"

        message_id = str(uuid.uuid4())
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
            }
        }
        request = SendMessageRequest(
            id=message_id,
            params=MessageSendParams.model_validate(payload),
        )
        response = await connection.send_message(request)
        print(f"[dev_host] ✅ Got reply from {agent_name}")
        return str(response)


async def _setup() -> Agent:
    host = DevHost(remote_agent_urls=[
        "http://localhost:10004",   # bug_finder
        "http://localhost:10005",   # code_writer
    ])
    return await host.create_agent()


root_agent = asyncio.get_event_loop().run_until_complete(_setup())
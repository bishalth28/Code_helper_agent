# Step 3: Agent Card — Code Writer
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn

from agent import CodeWriter          # FIX: was `from agent import MarkAgent` (wrong class)
from agent_executor import CodeWriterAgentExecutor


def main(host: str = "localhost", port: int = 10005):   # code_writer keeps 10005

    skill = AgentSkill(
        id="code_writer",
        name="Code Writer",
        description="Generates minimal, working code snippets from a prompt.",
        tags=["code", "generation", "writing"],
        examples=["Write a FastAPI endpoint that returns a list of users."],
    )

    agent_card = AgentCard(
        name="Code Writer",
        description="Generates minimal, working code snippets from a prompt.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=CodeWriter.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=CodeWriter.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=CodeWriterAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
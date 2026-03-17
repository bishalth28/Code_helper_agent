# Step 3: Agent Card — Bug Finder
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn

from agent import BugFinder
from agent_executor import BugFinderAgentExecutor


def main(host: str = "localhost", port: int = 10004):   # FIX: port 10004 (not 10005)

    skill = AgentSkill(
        id="bug_finder",
        name="Bug Finder",
        description="Reads error logs / tracebacks and suggests fixes.",
        tags=["code", "debugging", "bugs"],
        examples=["My FastAPI route raises a KeyError — here's the traceback."],
    )

    agent_card = AgentCard(
        name="Bug Finder",
        description="Reads error logs / tracebacks and suggests fixes.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=BugFinder.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=BugFinder.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=BugFinderAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
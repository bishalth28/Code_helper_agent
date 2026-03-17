# Step2: Agent Executor
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue

from a2a.server.tasks import TaskUpdater

from agent import CodeWriter
from a2a.types import Part, TextPart

class CodeWriterAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = CodeWriter()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        query = context.get_user_input()

        response = await self.agent.ask_agent(prompt_text=query)
        parts = [Part(root=TextPart(text=response))]

        await updater.add_artifact(parts, name="code_writer_result")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        return
import asyncio
import json
from typing import Union, Any, Self, Callable, Awaitable

import httpx

from gptscript.frame import PromptFrame, RunFrame, CallFrame, RunState, RunEventType, Program
from gptscript.opts import Options
from gptscript.tool import ToolDef, Tool


class Run:
    def __init__(self, subCommand: str, tools: Union[ToolDef | list[ToolDef] | str], opts: Options, gptscriptURL: str,
                 event_handlers: list[Callable[[Self, CallFrame | RunFrame | PromptFrame], Awaitable[None]]] = None):
        self.requestPath = subCommand
        self.tools = tools
        self.gptscriptURL = gptscriptURL
        self.event_handlers = event_handlers
        self.opts = opts
        if self.opts is None:
            self.opts = Options()

        self._state = RunState.Creating

        self.chatState: str = ""
        self._output: str = ""
        self._errput: str = ""
        self._err: str = ""
        self._aborted: bool = False
        self._program: Program | None = None
        self._calls: dict[str, CallFrame] | None = None
        self._parentCallID: str = ""
        self._rawOutput: Any = None
        self._task: Awaitable | None = None
        self._resp: httpx.Response | None = None
        self._event_tasks: list[Awaitable[None]] = []

    def program(self):
        return self._program

    def calls(self):
        return self._calls

    def parentCallID(self):
        return self._parentCallID

    def errOutput(self) -> str:
        return self._errput

    async def text(self) -> str:
        try:
            if self._task is not None:
                await self._task
        except Exception:
            self._state = RunState.Error
            if self._aborted:
                self._err = "Run was aborted"
        finally:
            self._task = None

        return f"run encountered an error: {self._err} with error output: {self._errput}" if self._err != "" else self._output

    def err(self):
        return self._err

    def state(self):
        return self._state

    def next_chat(self, input: str = "") -> Self:
        if self._state != RunState.Continue and self._state != RunState.Creating and self._state != RunState.Error:
            raise Exception(f"Run must in creating, continue or error state, not {self._state}")

        run = self
        if run.state != RunState.Creating:
            run = type(self)(self.requestPath, self.tools, self.opts, self.gptscriptURL,
                             event_handlers=self.event_handlers)

        if self.chatState and self._state == RunState.Continue:
            # Only update the chat state if the previous run didn't error.
            # The chat state on opts will be the chat state for the last successful run.
            run.opts.chatState = self.chatState

        run.opts.input = input
        if isinstance(run.tools, list):
            run._task = asyncio.create_task(
                run._request({"toolDefs": [tool.to_json() for tool in run.tools], **vars(run.opts)}))
        elif isinstance(run.tools, str) and run.tools != "":
            run._task = asyncio.create_task(run._request({"file": run.tools, **vars(run.opts)}))
        elif isinstance(run.tools, ToolDef) or isinstance(run.tools, Tool):
            # In this last case, this.tools is a single ToolDef.
            run._task = asyncio.create_task(run._request({"toolDefs": [run.tools.to_json()], **vars(run.opts)}))
        else:
            run._task = asyncio.create_task(run._request({**vars(run.opts)}))

        return run

    async def _request(self, tool: Any):
        if self._state.is_terminal():
            raise Exception("run is in terminal state and cannot be run again: state " + str(self._state))

        # Use a timeout of 15 minutes = 15 * 60s.
        async with httpx.AsyncClient(timeout=httpx.Timeout(15 * 60.0)) as client:
            method = "GET" if tool is None else "POST"

            async with client.stream(method, self.gptscriptURL + "/" + self.requestPath, json=tool) as resp:
                self._resp = resp
                self._state = RunState.Running
                done = True
                if resp.status_code < 200 or resp.status_code >= 400:
                    self._state = RunState.Error
                    self._err = "run encountered an error"

                async for line in resp.aiter_lines():
                    line = line.strip()
                    line = line.removeprefix("data: ")
                    line = line.strip()
                    if line == "" or line == "[DONE]":
                        continue

                    data = json.loads(line)

                    if "stdout" in data:
                        if isinstance(data["stdout"], str):
                            self._output = data["stdout"]
                        else:
                            if isinstance(self, RunBasicCommand):
                                self._output = json.dumps(data["stdout"])
                            else:
                                self.chatState = json.dumps(data["stdout"]["state"])
                                if "content" in data["stdout"]:
                                    self._output = data["stdout"]["content"]

                                done = data["stdout"].get("done", False)
                                self._rawOutput = data["stdout"]
                    elif "stderr" in data:
                        self._errput += data["stderr"]
                    else:
                        if "prompt" in data:
                            event = PromptFrame(**data["prompt"])

                            # If a prmpt happens, but the call didn't explicitly allow it, then we error.
                            if not self.opts.prompt:
                                self._err = f"prompt event occurred when prompt was not allowed: {event.__dict__}"
                                await self.aclose()
                                break
                        elif "run" in data:
                            event = RunFrame(**data["run"])
                            if event.type == RunEventType.runStart:
                                self._program = event.program
                            elif event.type == RunEventType.runFinish and event.error != "":
                                self._err = event.error
                        else:
                            event = CallFrame(**data["call"])
                            if self._calls is None:
                                self._calls = {}
                            self._calls[event.id] = event
                            if event.parentID == "" and self._parentCallID == "":
                                self._parentCallID = event.id
                        if self.event_handlers is not None:
                            for event_handler in self.event_handlers:
                                self._event_tasks.append(asyncio.create_task(event_handler(self, event)))

        self._resp = None
        if self._err != "":
            self._state = RunState.Error
        elif done:
            self._state = RunState.Finished
        else:
            self._state = RunState.Continue

        for task in self._event_tasks:
            try:
                await task
            except Exception as e:
                print(f"error during event processing: {e}")

        self._event_tasks = []

    async def aclose(self):
        if self._task is None or self._resp is None:
            raise Exception("run not started")
        elif not self._aborted:
            self._aborted = True
            await self._resp.aclose()


class RunBasicCommand(Run):
    def __init__(self, subCommand: str, request_body: Any, gptscriptURL: str):
        super().__init__(subCommand, "", Options(), gptscriptURL)
        self.request_body = request_body

    def next_chat(self, input: str = "") -> Self:
        if self._state != RunState.Creating:
            raise Exception(f"A basic command run must in creating, not {self._state}")

        self.opts.input = input
        self._task = self._request(self.request_body)

        return self

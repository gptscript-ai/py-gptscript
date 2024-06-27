import json
import platform
import os
from socket import socket
from subprocess import Popen, PIPE
from sys import executable
from time import sleep
from typing import Any, Callable, Awaitable

import requests

from gptscript.confirm import AuthResponse
from gptscript.frame import RunFrame, CallFrame, PromptFrame
from gptscript.opts import GlobalOptions
from gptscript.prompt import PromptResponse
from gptscript.run import Run, RunBasicCommand, Options
from gptscript.text import Text
from gptscript.tool import ToolDef, Tool


class GPTScript:
    __gptscript_count = 0
    __server_url = ""
    __process: Popen = None
    __server_ready: bool = False

    def __init__(self, opts: GlobalOptions = None):
        if opts is None:
            opts = GlobalOptions()
        GPTScript.__gptscript_count += 1

        if GPTScript.__server_url == "":
            GPTScript.__server_url = os.environ.get("GPTSCRIPT_URL", "")

        if GPTScript.__gptscript_count == 1 and os.environ.get("GPTSCRIPT_DISABLE_SERVER", "") != "true":
            if GPTScript.__server_url == "":
                with socket() as s:
                    s.bind(("", 0))
                    GPTScript.__server_url = f"127.0.0.1:{s.getsockname()[1]}"

            opts.toEnv()

            GPTScript.__process = Popen(
                [_get_command(), "--listen-address", GPTScript.__server_url, "sdkserver"],
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                env=opts.Env,
                text=True,
                encoding="utf-8",
            )

        self._server_url = f"http://{GPTScript.__server_url}"
        self._wait_for_gptscript()

    def _wait_for_gptscript(self):
        if not GPTScript.__server_ready:
            for _ in range(0, 20):
                try:
                    resp = requests.get(self._server_url + "/healthz")
                    if resp.status_code == 200:
                        GPTScript.__server_ready = True
                        return
                except requests.exceptions.ConnectionError:
                    pass

                sleep(1)

            raise Exception("Failed to start gptscript")

    def close(self):
        GPTScript.__gptscript_count -= 1
        if GPTScript.__gptscript_count == 0 and GPTScript.__process is not None:
            GPTScript.__process.stdin.close()
            GPTScript.__process.wait()
            GPTScript.__server_ready = False
            GPTScript.__process = None
            self._server_url = ""

    def evaluate(
            self,
            tool: ToolDef | list[ToolDef],
            opts: Options = None,
            event_handlers: list[Callable[[Run, CallFrame | RunFrame | PromptFrame], Awaitable[None]]] = None
    ) -> Run:
        return Run("evaluate", tool, opts, self._server_url, event_handlers=event_handlers).next_chat(
            "" if opts is None else opts.input
        )

    def run(
            self, tool_path: str,
            opts: Options = None,
            event_handlers: list[Callable[[Run, CallFrame | RunFrame | PromptFrame], Awaitable[None]]] = None
    ) -> Run:
        return Run("run", tool_path, opts, self._server_url, event_handlers=event_handlers).next_chat(
            "" if opts is None else opts.input
        )

    async def parse(self, file_path: str) -> list[Text | Tool]:
        out = await self._run_basic_command("parse", {"file": file_path})
        parsed_nodes = json.loads(out)
        return [Text(**node["textNode"]) if "textNode" in node else Tool(**node.get("toolNode", {}).get("tool", {})) for
                node in parsed_nodes.get("nodes", [])]

    async def parse_tool(self, tool_def: str) -> list[Text | Tool]:
        out = await self._run_basic_command("parse", {"content": tool_def})
        parsed_nodes = json.loads(out)
        return [Text(**node["textNode"]) if "textNode" in node else Tool(**node.get("toolNode", {}).get("tool", {})) for
                node in parsed_nodes.get("nodes", [])]

    async def fmt(self, nodes: list[Text | Tool]) -> str:
        request_nodes = []
        for node in nodes:
            request_nodes.append(node.to_json())
        return await self._run_basic_command("fmt", {"nodes": request_nodes})

    async def confirm(self, resp: AuthResponse):
        await self._run_basic_command("confirm/" + resp.id, {**vars(resp)})

    async def prompt(self, resp: PromptResponse):
        await self._run_basic_command("prompt-response/" + resp.id, resp.responses)

    async def _run_basic_command(self, sub_command: str, request_body: Any = None):
        run = RunBasicCommand(sub_command, request_body, self._server_url)

        run.next_chat()

        out = await run.text()
        if run.err() != "":
            return f"an error occurred: {out}"

        return out

    async def version(self) -> str:
        return await self._run_basic_command("version")

    async def list_tools(self) -> str:
        return await self._run_basic_command("list-tools")

    async def list_models(self) -> list[str]:
        return (await self._run_basic_command("list-models")).split("\n")


def _get_command():
    if os.getenv("GPTSCRIPT_BIN") is not None:
        return os.getenv("GPTSCRIPT_BIN")

    bin_path = os.path.join(os.path.dirname(executable), "gptscript")
    if platform.system() == "Windows":
        bin_path += ".exe"

    return bin_path if os.path.exists(bin_path) else "gptscript"

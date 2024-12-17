import base64
import json
import os
import platform
from subprocess import Popen, PIPE
from sys import executable
from typing import Any, Callable, Awaitable, List

from gptscript.confirm import AuthResponse
from gptscript.credentials import Credential, to_credential
from gptscript.datasets import DatasetElementMeta, DatasetElement, DatasetMeta
from gptscript.fileinfo import FileInfo
from gptscript.frame import RunFrame, CallFrame, PromptFrame, Program
from gptscript.openai import Model
from gptscript.opts import GlobalOptions
from gptscript.prompt import PromptResponse
from gptscript.run import Run, RunBasicCommand, Options
from gptscript.text import Text
from gptscript.tool import ToolDef, Tool


class GPTScript:
    __gptscript_count = 0
    __server_url = ""
    __process: Popen = None

    def __init__(self, opts: GlobalOptions = None):
        if opts is None:
            opts = GlobalOptions()
        self.opts = opts

        start_sdk = GPTScript.__process is None and GPTScript.__server_url == "" and self.opts.URL == ""
        GPTScript.__gptscript_count += 1
        if GPTScript.__server_url == "":
            GPTScript.__server_url = os.environ.get("GPTSCRIPT_URL", "")
            start_sdk = start_sdk and GPTScript.__server_url == ""

        if start_sdk:
            self.opts.toEnv()

            GPTScript.__process = Popen(
                [_get_command(), "sys.sdkserver", "--listen-address", "127.0.0.1:0"],
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                env={e.split("=", 1)[0]: e.split("=", 1)[1] for e in self.opts.Env},
                text=True,
                encoding="utf-8",
            )

            GPTScript.__server_url = GPTScript.__process.stderr.readline().strip("\n")
            if "=" in GPTScript.__server_url:
                GPTScript.__server_url = GPTScript.__server_url.split("=")[1]

        if self.opts.URL == "":
            self.opts.URL = GPTScript.__server_url
        if not (self.opts.URL.startswith("http://") or self.opts.URL.startswith("https://")):
            self.opts.URL = f"http://{self.opts.URL}"

        self.opts.Env.append("GPTSCRIPT_URL=" + self.opts.URL)

        if self.opts.Token == "":
            self.opts.Token = os.environ.get("GPTSCRIPT_TOKEN", "")
        if self.opts.Token != "":
            self.opts.Env.append("GPTSCRIPT_TOKEN=" + self.opts.Token)

    def close(self):
        GPTScript.__gptscript_count -= 1
        if GPTScript.__gptscript_count == 0 and GPTScript.__process is not None:
            GPTScript.__process.stdin.close()
            GPTScript.__process.wait()
            GPTScript.__process = None
            self.opts = None

    def evaluate(
            self,
            tool: ToolDef | list[ToolDef],
            opts: Options = None,
            event_handlers: list[Callable[[Run, CallFrame | RunFrame | PromptFrame], Awaitable[None]]] = None
    ) -> Run:
        opts = opts if opts is not None else Options()
        return Run(
            "evaluate",
            tool,
            opts.merge_global_opts(self.opts),
            event_handlers=event_handlers,
        ).next_chat(opts.input)

    def run(
            self, tool_path: str,
            opts: Options = None,
            event_handlers: list[Callable[[Run, CallFrame | RunFrame | PromptFrame], Awaitable[None]]] = None
    ) -> Run:
        opts = opts if opts is not None else Options()
        return Run(
            "run",
            tool_path,
            opts.merge_global_opts(self.opts),
            event_handlers=event_handlers,
        ).next_chat(opts.input)

    async def load_file(self, file_path: str, disable_cache: bool = False, sub_tool: str = '') -> Program:
        out = await self._run_basic_command(
            "load",
            {"file": file_path, "disableCache": disable_cache, "subTool": sub_tool},
        )
        parsed_nodes = json.loads(out)
        return Program(**parsed_nodes.get("program", {}))

    async def load_content(self, content: str, disable_cache: bool = False, sub_tool: str = '') -> Program:
        out = await self._run_basic_command(
            "load",
            {"content": content, "disableCache": disable_cache, "subTool": sub_tool},
        )
        parsed_nodes = json.loads(out)
        return Program(**parsed_nodes.get("program", {}))

    async def load_tools(self, tool_defs: list[ToolDef], disable_cache: bool = False, sub_tool: str = '') -> Program:
        out = await self._run_basic_command(
            "load",
            {"toolDefs": [t.to_json() for t in tool_defs], "disableCache": disable_cache, "subTool": sub_tool},
        )
        parsed_nodes = json.loads(out)
        return Program(**parsed_nodes.get("program", {}))

    async def parse(self, file_path: str, disable_cache: bool = False) -> list[Text | Tool]:
        out = await self._run_basic_command("parse", {"file": file_path, "disableCache": disable_cache})
        parsed_nodes = json.loads(out)
        if parsed_nodes is None or parsed_nodes.get("nodes", None) is None:
            return []
        return [Text(**node["textNode"]) if "textNode" in node else Tool(**node.get("toolNode", {}).get("tool", {})) for
                node in parsed_nodes.get("nodes", [])]

    async def parse_content(self, content: str) -> list[Text | Tool]:
        out = await self._run_basic_command("parse", {"content": content})
        parsed_nodes = json.loads(out)
        if parsed_nodes is None or parsed_nodes.get("nodes", None) is None:
            return []
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
        run = RunBasicCommand(sub_command, request_body, self.opts.URL, self.opts.Token)

        run.next_chat()

        out = await run.text()
        if run.err() != "":
            return f"an error occurred: {out}"

        return out

    async def version(self) -> str:
        return await self._run_basic_command("version")

    async def list_models(self, providers: list[str] = None, credential_overrides: list[str] = None) -> list[Model]:
        if self.opts.DefaultModelProvider != "":
            if providers is None:
                providers = []
            providers.append(self.opts.DefaultModelProvider)

        res = await self._run_basic_command(
            "list-models",
            {"providers": providers, "credentialOverrides": credential_overrides}
        )
        return [Model(**model) for model in json.loads(res)]

    async def list_credentials(self, contexts: List[str] = None, all_contexts: bool = False) -> list[Credential] | str:
        if contexts is None:
            contexts = ["default"]

        res = await self._run_basic_command(
            "credentials",
            {"context": contexts, "allContexts": all_contexts}
        )
        if res.startswith("an error occurred:"):
            return res

        return [to_credential(cred) for cred in json.loads(res)]

    async def create_credential(self, cred: Credential) -> str:
        return await self._run_basic_command(
            "credentials/create",
            {"content": cred.to_json()}
        )

    async def reveal_credential(self, contexts: List[str] = None, name: str = "") -> Credential | str:
        if contexts is None:
            contexts = ["default"]

        res = await self._run_basic_command(
            "credentials/reveal",
            {"context": contexts, "name": name}
        )
        if res.startswith("an error occurred:"):
            return res

        return to_credential(json.loads(res))

    async def delete_credential(self, context: str = "default", name: str = "") -> str:
        return await self._run_basic_command(
            "credentials/delete",
            {"context": [context], "name": name}
        )

    # list_datasets returns an array of dataset IDs
    async def list_datasets(self) -> List[DatasetMeta]:
        res = await self._run_basic_command(
            "datasets",
            {
                "input": "{}",
                "datasetTool": self.opts.DatasetTool,
                "env": self.opts.Env
            }
        )
        return [DatasetMeta.model_validate(d) for d in json.loads(res)]

    async def add_dataset_elements(
            self,
            elements: List[DatasetElement],
            datasetID: str = "",
            name: str = "",
            description: str = ""
    ) -> str:
        if not elements:
            raise ValueError("elements cannot be empty")

        res = await self._run_basic_command(
            "datasets/add-elements",
            {
                "input": json.dumps({
                    "datasetID": datasetID,
                    "name": name,
                    "description": description,
                    "elements": [element.model_dump() for element in elements],
                }),
                "datasetTool": self.opts.DatasetTool,
                "env": self.opts.Env
            }
        )
        return res

    async def list_dataset_elements(self, datasetID: str) -> List[DatasetElementMeta]:
        if datasetID == "":
            raise ValueError("datasetID cannot be empty")

        res = await self._run_basic_command(
            "datasets/list-elements",
            {
                "input": json.dumps({"datasetID": datasetID}),
                "datasetTool": self.opts.DatasetTool,
                "env": self.opts.Env
            }
        )
        return [DatasetElementMeta.model_validate(d) for d in json.loads(res)]

    async def get_dataset_element(self, datasetID: str, elementName: str) -> DatasetElement:
        if datasetID == "":
            raise ValueError("datasetID cannot be empty")
        elif elementName == "":
            raise ValueError("elementName cannot be empty")

        res = await self._run_basic_command(
            "datasets/get-element",
            {
                "input": json.dumps({
                    "datasetID": datasetID,
                    "name": elementName,
                }),
                "datasetTool": self.opts.DatasetTool,
                "env": self.opts.Env,
            }
        )
        return DatasetElement.model_validate_json(res)

    async def create_workspace(self, provider_type: str, from_workspaces: list[str] = None) -> str:
        return await self._run_basic_command(
            "workspaces/create",
            {
                "providerType": provider_type,
                "fromWorkspaces": from_workspaces,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        )

    async def delete_workspace(self, workspace_id: str):
        if workspace_id == "":
            raise ValueError("workspace_id cannot be empty")

        await self._run_basic_command(
            "workspaces/delete",
            {
                "id": workspace_id,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        )

    async def list_files_in_workspace(self, workspace_id: str = "", prefix: str = "") -> List[str]:
        if workspace_id == "":
            workspace_id = os.environ["GPTSCRIPT_WORKSPACE_ID"]

        return json.loads(await self._run_basic_command(
            "workspaces/list",
            {
                "id": workspace_id,
                "prefix": prefix,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        ))

    async def remove_all(self, workspace_id: str = "", with_prefix: str = ""):
        if workspace_id == "":
            workspace_id = os.environ["GPTSCRIPT_WORKSPACE_ID"]

        await self._run_basic_command(
            "workspaces/remove-all-with-prefix",
            {
                "id": workspace_id,
                "prefix": with_prefix,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        )

    async def write_file_in_workspace(self, file_path: str, contents: bytes, workspace_id: str = ""):
        if workspace_id == "":
            workspace_id = os.environ["GPTSCRIPT_WORKSPACE_ID"]

        await self._run_basic_command(
            "workspaces/write-file",
            {
                "id": workspace_id,
                "filePath": file_path,
                "contents": base64.b64encode(contents).decode("utf-8") if contents is not None else None,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        )

    async def delete_file_in_workspace(self, file_path: str, workspace_id: str = ""):
        if workspace_id == "":
            workspace_id = os.environ["GPTSCRIPT_WORKSPACE_ID"]

        await self._run_basic_command(
            "workspaces/delete-file",
            {
                "id": workspace_id,
                "filePath": file_path,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        )

    async def read_file_in_workspace(self, file_path: str, workspace_id: str = "") -> bytes:
        if workspace_id == "":
            workspace_id = os.environ["GPTSCRIPT_WORKSPACE_ID"]

        return base64.b64decode(await self._run_basic_command(
            "workspaces/read-file",
            {
                "id": workspace_id,
                "filePath": file_path,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        ))

    async def stat_file_in_workspace(self, file_path: str, workspace_id: str = "") -> FileInfo:
        if workspace_id == "":
            workspace_id = os.environ["GPTSCRIPT_WORKSPACE_ID"]

        return FileInfo.model_validate_json(await self._run_basic_command(
            "workspaces/stat-file",
            {
                "id": workspace_id,
                "filePath": file_path,
                "workspaceTool": self.opts.WorkspaceTool,
                "env": self.opts.Env,
            }
        ))


def _get_command():
    if os.getenv("GPTSCRIPT_BIN") is not None:
        return os.getenv("GPTSCRIPT_BIN")

    bin_path = os.path.join(os.path.dirname(executable), "gptscript")
    if platform.system() == "Windows":
        bin_path += ".exe"

    return bin_path if os.path.exists(bin_path) else "gptscript"

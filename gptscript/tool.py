from typing import Any


class Property:
    def __init__(self,
                 type: str = "string",
                 description: str = "",
                 default: str = "",
                 ):
        self.type = type
        self.description = description
        self.default = default

    def to_json(self):
        return self.__dict__


class ArgumentSchema:
    def __init__(self,
                 type: str = "object",
                 properties: dict[str, Property] = None,
                 required: list[str] = None,
                 ):
        self.type = type
        self.properties = properties
        if self.properties is not None:
            for prop in self.properties:
                if isinstance(self.properties[prop], dict):
                    self.properties[prop] = Property(**self.properties[prop])
        self.required = required

    def to_json(self):
        out = self.__dict__
        for prop in self.properties:
            out["properties"][prop] = self.properties[prop].to_json()

        return out


class ToolDef:
    def __init__(self,
                 name: str = "",
                 description: str = "",
                 maxTokens: int = 0,
                 modelName: str = "",
                 modelProvider: bool = False,
                 jsonResponse: bool = False,
                 temperature: int | None = None,
                 cache: bool | None = None,
                 chat: bool = False,
                 internalPrompt: bool | None = None,
                 arguments: ArgumentSchema = None,
                 tools: list[str] = None,
                 globalTools: list[str] = None,
                 globalModelName: str = "",
                 context: list[str] = None,
                 exportContext: list[str] = None,
                 export: list[str] = None,
                 agents: list[str] = None,
                 credentials: list[str] = None,
                 instructions: str = "",
                 ):
        self.name = name
        self.description = description
        self.maxTokens = maxTokens
        self.modelName = modelName
        self.modelProvider = modelProvider
        self.jsonResponse = jsonResponse
        self.temperature = temperature
        self.cache = cache
        self.chat = chat
        self.internalPrompt = internalPrompt
        self.arguments = arguments
        if self.arguments is not None:
            if isinstance(self.arguments, dict):
                self.arguments = ArgumentSchema(**self.arguments)
        self.tools = tools
        self.globalTools = globalTools
        self.globalModelName = globalModelName
        self.context = context
        self.exportContext = exportContext
        self.export = export
        self.agents = agents
        self.credentials = credentials
        self.instructions = instructions

    def to_json(self) -> dict[str, Any]:
        out = self.__dict__
        if self.arguments is not None:
            out["arguments"] = self.arguments.to_json()
        return out


class ToolReference:
    def __init__(self,
                 named: str = "",
                 reference: str = "",
                 arg: str = "",
                 toolID: str = "",
                 ):
        self.named = named
        self.reference = reference
        self.arg = arg
        self.toolID = toolID

    def to_json(self) -> dict[str, Any]:
        return self.__dict__


class Repo:
    def __init__(self,
                 VCS: str = "",
                 Root: str = "",
                 Path: str = "",
                 Name: str = "",
                 Revision: str = "",
                 ):
        self.VCS = VCS
        self.Root = Root
        self.Path = Path
        self.Name = Name
        self.Revision = Revision


class SourceRef:
    def __init__(self,
                 location: str = "",
                 lineNo: int = 0,
                 repo: Repo = None,
                 ):
        self.location = location
        self.lineNo = lineNo
        self.repo = repo
        if self.repo is not None and isinstance(self.repo, dict):
            self.repo = Repo(**self.repo)

    def to_json(self) -> dict[str, Any]:
        return self.__dict__


class Tool(ToolDef):
    def __init__(self,
                 id: str = "",
                 name: str = "",
                 description: str = "",
                 maxTokens: int = 0,
                 modelName: str = "",
                 modelProvider: bool = False,
                 jsonResponse: bool = False,
                 temperature: int | None = None,
                 cache: bool | None = None,
                 chat: bool = False,
                 internalPrompt: bool | None = None,
                 arguments: ArgumentSchema = None,
                 tools: list[str] = None,
                 globalTools: list[str] = None,
                 globalModelName: str = "",
                 context: list[str] = None,
                 exportContext: list[str] = None,
                 export: list[str] = None,
                 agents: list[str] = None,
                 credentials: list[str] = None,
                 instructions: str = "",
                 toolMapping: dict[str, list[ToolReference]] = None,
                 localTools: dict[str, str] = None,
                 source: SourceRef = None,
                 workingDir: str = "",
                 ):
        super().__init__(name, description, maxTokens, modelName, modelProvider, jsonResponse, temperature, cache, chat,
                         internalPrompt, arguments, tools, globalTools, globalModelName, context, exportContext, export,
                         agents, credentials, instructions)

        self.id = id
        self.toolMapping = toolMapping
        if self.toolMapping is not None:
            for tool in self.toolMapping:
                if self.toolMapping[tool] is not None:
                    for i in range(len(self.toolMapping[tool])):
                        if isinstance(self.toolMapping[tool][i], dict):
                            self.toolMapping[tool][i] = ToolReference(**self.toolMapping[tool][i])
        self.localTools = localTools
        self.source = source
        if self.source is not None and isinstance(self.source, dict):
            self.source = SourceRef(**self.source)
        self.workingDir = workingDir

    def to_json(self) -> Any:
        tool_dict = super().to_json()
        tool_dict["id"] = self.id
        tool_dict["workingDir"] = self.workingDir
        tool_dict["localTools"] = self.localTools

        if self.toolMapping is not None:
            for tool_map in self.toolMapping:
                for i in range(len(self.toolMapping[tool_map])):
                    tool_dict["toolMapping"][tool_map][i] = self.toolMapping[tool_map][i].to_json()

        if self.source is not None:
            tool_dict["source"] = self.source.to_json()

        return {"toolNode": {"tool": tool_dict}}

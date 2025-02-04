from enum import Enum
from typing import Any

from gptscript.tool import Tool, ToolReference


class RunEventType(Enum):
    event = "event",
    runStart = "runStart",
    runFinish = "runFinish",
    callStart = "callStart",
    callChat = "callChat",
    callSubCalls = "callSubCalls",
    callProgress = "callProgress",
    callConfirm = "callConfirm",
    callContinue = "callContinue",
    callFinish = "callFinish",
    prompt = "prompt"


class ToolCategory(Enum):
    provider = "provider",
    credential = "credential",
    context = "context",
    input = "input",
    output = "output",
    none = ""


class RunState(Enum):
    Creating = "creating",
    Running = "running",
    Continue = "continue",
    Finished = "finished",
    Error = "error"

    def is_terminal(self):
        return self.value == RunState.Error or self.value == RunState.Finished


class Program:
    def __init__(self,
                 name: str = "",
                 entryToolId: str = "",
                 toolSet: dict[str, Tool] = None,
                 **kwargs,
                 ):
        self.name = name
        self.entryToolId = entryToolId
        self.toolSet = toolSet
        if self.toolSet is None:
            self.toolSet = {}
        else:
            for tool in toolSet:
                if isinstance(self.toolSet[tool], dict):
                    self.toolSet[tool] = Tool(**self.toolSet[tool])


class RunFrame:
    def __init__(self,
                 id: str = "",
                 type: RunEventType = RunEventType.runStart,
                 program: Program = None,
                 input: str = "",
                 output: str = "",
                 error: str = "",
                 start: str = "",
                 end: str = "",
                 state: RunState = RunState.Creating,
                 chatState: str = "",
                 **kwargs,
                 ):
        self.id = id
        self.type = type
        if isinstance(self.type, str):
            self.type = RunEventType[self.type]
        self.program = program
        if isinstance(self.program, dict):
            self.program = Program(**self.program)
        self.input = input
        self.output = output
        self.error = error
        self.start = start
        self.end = end
        self._state = state
        self.chatState = chatState


class Call:
    def __init__(self,
                 toolID: str = "",
                 input: str = "",
                 **kwargs,
                 ):
        self.toolID = toolID
        self.input = input


class Output:
    def __init__(self,
                 content: str = "",
                 subCalls: dict[str, Call] = None,
                 **kwargs,
                 ):
        self.content = content
        self.subCalls = subCalls


class InputContext:
    def __init__(self,
                 toolID: str = "",
                 content: str = "",
                 **kwargs,
                 ):
        self.toolID = toolID
        self.content = content


class Usage:
    def __init__(self,
                 promptTokens: int = 0,
                 completionTokens: int = 0,
                 totalTokens: int = 0,
                 **kwargs,
                 ):
        self.promptTokens = promptTokens
        self.completionTokens = completionTokens
        self.totalTokens = totalTokens


class CallFrame:
    def __init__(self,
                 id: str = "",
                 tool: Tool = None,
                 agentGroup: list[ToolReference] = None,
                 currentAgent: ToolReference = None,
                 displayText: str = "",
                 inputContext: list[InputContext] = None,
                 toolCategory: ToolCategory = ToolCategory.none,
                 toolName: str = "",
                 parentID: str = "",
                 type: RunEventType = RunEventType.event,
                 start: str = "",
                 end: str = "",
                 input: str = "",
                 output: list[Output] = None,
                 error: str = "",
                 usage: Usage = None,
                 chatResponseCached: bool = False,
                 toolResults: int = 0,
                 llmRequest: Any = None,
                 llmResponse: Any = None,
                 **kwargs,
                 ):
        self.id = id
        self.tool = tool
        self.agentGroup = agentGroup
        if self.agentGroup is not None:
            for i in range(len(self.agentGroup)):
                if isinstance(self.agentGroup[i], dict):
                    self.agentGroup[i] = ToolReference(**self.agentGroup[i])
        self.currentAgent = currentAgent
        if self.currentAgent is not None and isinstance(self.currentAgent, dict):
            self.currentAgent = ToolReference(**self.currentAgent)
        self.displayText = displayText
        self.inputContext = inputContext
        if self.inputContext is not None:
            for i in range(len(self.inputContext)):
                if isinstance(self.inputContext[i], dict):
                    self.inputContext[i] = InputContext(**self.inputContext[i])
        self.toolCategory = toolCategory
        if isinstance(self.toolCategory, str):
            self.toolCategory = ToolCategory.none if self.toolCategory == "" else ToolCategory[self.toolCategory]
        self.toolName = toolName
        self.parentID = parentID
        self.type = type
        if isinstance(self.type, str):
            self.type = RunEventType[self.type]
        self.start = start
        self.end = end
        self.input = input
        self.output = output
        if self.output is not None:
            for i in range(len(self.output)):
                if isinstance(self.output[i], dict):
                    self.output[i] = Output(**self.output[i])
        self.error = error
        self.usage = usage
        if isinstance(self.usage, dict):
            self.usage = Usage(**self.usage)
        self.chatResponseCached = chatResponseCached
        self.toolResults = toolResults
        self.llmRequest = llmRequest
        self.llmResponse = llmResponse


class PromptField:
    def __init__(self,
                 name: str = "",
                 description: str = "",
                 sensitive: bool | None = None,
                 **kwargs,
                 ):
        self.name = name
        self.description = description
        self.sensitive = sensitive


class PromptFrame:
    def __init__(self,
                 id: str = "",
                 type: RunEventType = RunEventType.prompt,
                 time: str = "",
                 message: str = "",
                 fields: list[PromptField] = None,
                 metadata: dict[str, str] = None,
                 sensitive: bool = False,
                 **kwargs,
                 ):
        self.id = id
        self.time = time
        self.message = message
        self.fields = fields
        if self.fields is not None:
            for i in range(len(self.fields)):
                if isinstance(self.fields[i], dict):
                    self.fields[i] = PromptField(**self.fields[i])
        self.metadata = metadata
        self.sensitive = sensitive
        self.type = type
        if isinstance(self.type, str):
            self.type = RunEventType[self.type]

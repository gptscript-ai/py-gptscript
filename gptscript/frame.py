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
                 ):
        self.name = name
        self.entryToolId = entryToolId
        self.toolSet = toolSet
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
                 ):
        self.toolID = toolID
        self.input = input


class Output:
    def __init__(self,
                 content: str = "",
                 subCalls: dict[str, Call] = None,
                 ):
        self.content = content
        self.subCalls = subCalls


class InputContext:
    def __init__(self,
                 toolID: str = "",
                 content: str = "",
                 ):
        self.toolID = toolID
        self.content = content


class Usage:
    def __init__(self,
                 promptTokens: int = 0,
                 completionTokens: int = 0,
                 totalTokens: int = 0,
                 ):
        self.promptTokens = promptTokens
        self.completionTokens = completionTokens
        self.totalTokens = totalTokens


class CallFrame:
    def __init__(self,
                 id: str = "",
                 tool: Tool = None,
                 agentGroup: list[ToolReference] = None,
                 displayText: str = "",
                 inputContext: list[InputContext] = None,
                 toolCategory: str = "",
                 toolName: str = "",
                 parentID: str = "",
                 type: RunEventType = RunEventType.event,
                 start: str = "",
                 end: str = "",
                 input: str = "",
                 output: list[Output] = None,
                 error: str = "",
                 usage: Usage = None,
                 llmRequest: Any = None,
                 llmResponse: Any = None,
                 ):
        self.id = id
        self.tool = tool
        self.agentGroup = agentGroup
        if self.agentGroup is not None:
            for i in range(len(self.agentGroup)):
                if isinstance(self.agentGroup[i], dict):
                    self.agentGroup[i] = ToolReference(**self.agentGroup[i])
        self.displayText = displayText
        self.inputContext = inputContext
        if self.inputContext is not None:
            for i in range(len(self.inputContext)):
                if isinstance(self.inputContext[i], dict):
                    self.inputContext[i] = InputContext(**self.inputContext[i])
        self.toolCategory = toolCategory
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
        self.llmRequest = llmRequest
        self.llmResponse = llmResponse


class PromptFrame:
    def __init__(self,
                 id: str = "",
                 type: RunEventType = RunEventType.prompt,
                 time: str = "",
                 message: str = "",
                 fields: list[str] = None,
                 sensitive: bool = False,
                 ):
        self.id = id
        self.time = time
        self.message = message
        self.fields = fields
        self.sensitive = sensitive
        self.type = type
        if isinstance(self.type, str):
            self.type = RunEventType[self.type]

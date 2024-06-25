# GPTScript Python Module

## Introduction

The GPTScript Python module is a library that provides a simple interface to create and run gptscripts within Python
applications, and Jupyter notebooks. It allows you to define tools, execute them, and process the responses.

## Installation

You can install the GPTScript Python module using pip.

```bash
pip install gptscript
```

On MacOS, Windows X6

### SDIST and none-any wheel installations

When installing from the sdist or the none-any wheel, the binary is not packaged by default. You must run the
install_gptscript command to install the binary.

```bash
install_gptscript
```

The script is added to the same bin directory as the python executable, so it should be in your path.

Or you can install the gptscript cli from your code by running:

```python
from gptscript.install import install

install()
```

### Using an existing gptscript cli

If you already have the gptscript cli installed, you can use it by setting the envvar:

```bash
export GPTSCRIPT_BIN="/path/to/gptscript"
```

## GPTScript

The GPTScript instance allows the caller to run gptscript files, tools, and other operations (see below). Note that the
intention is that a single GPTScript instance is all you need for the life of your application, you should
call `close()` on the instance when you are done.

## Global Options

When creating a `GTPScript` instance, you can pass the following global options. These options are also available as
run `Options`. Anything specified as a run option will take precedence over the global option.

- `APIKey`: Specify an OpenAI API key for authenticating requests. Defaults to `OPENAI_API_KEY` environment variable
- `BaseURL`: A base URL for an OpenAI compatible API (the default is `https://api.openai.com/v1`)
- `DefaultModel`: The default model to use for OpenAI requests
- `Env`: Supply the environment variables. Supplying anything here means that nothing from the environment is used. The
  default is `os.environ()`. Supplying `Env` at the run/evaluate level will be treated as "additional."

## Run Options

These are optional options that can be passed to the `run` and `evaluate` functions.
None of the options is required, and the defaults will reduce the number of calls made to the Model API.
As noted above, the Global Options are also available to specify here. These options would take precedence.

- `disableCache`: Enable or disable caching. Default (False).
- `subTool`: Use tool of this name, not the first tool
- `input`: Input arguments for the tool run
- `workspace`: Directory to use for the workspace, if specified it will not be deleted on exit
- `chatState`: The chat state to continue, or null to start a new chat and return the state
- `confirm`: Prompt before running potentially dangerous commands
- `prompt`: Allow prompting of the user

## Tools

The `Tool` class represents a gptscript tool. The fields align with what you would be able to define in a normal
gptscript .gpt file.

### Fields

- `name`: The name of the tool.
- `description`: A description of the tool.
- `tools`: Additional tools associated with the main tool.
- `maxTokens`: The maximum number of tokens to generate.
- `model`: The GPT model to use.
- `cache`: Whether to use caching for responses.
- `temperature`: The temperature parameter for response generation.
- `arguments`: Additional arguments for the tool.
- `internalPrompt`: Optional boolean defaults to None.
- `instructions`: Instructions or additional information about the tool.
- `jsonResponse`: Whether the response should be in JSON format.(If you set this to True, you must say 'json' in the
  instructions as well.)

## Primary Functions

Aside from the list methods there are `exec` and `exec_file` methods that allow you to execute a tool and get the
responses. Those functions also provide a streaming version of execution if you want to process the output streams in
your code as the tool is running.

### `list_tools()`

This function lists the available tools.

```python
from gptscript.gptscript import GPTScript


async def list_tools():
    gptscript = GPTScript()
    tools = await gptscript.list_tools()
    print(tools)
    gptscript.close()
```

### `list_models()`

This function lists the available GPT models.

```python
from gptscript.gptscript import GPTScript


async def list_models():
    gptscript = GPTScript()
    tools = await gptscript.list_models()
    print(tools)
    gptscript.close()
```

### `parse()`

Parse a file into a Tool data structure.

```python
from gptscript.gptscript import GPTScript


async def parse_example():
    gptscript = GPTScript()
    tools = await gptscript.parse("/path/to/file")
    print(tools)
    gptscript.close()
```

### `parse_tool()`

Parse the contents that represents a GPTScript file into a Tool data structure.

```python
from gptscript.gptscript import GPTScript


async def parse_tool_example():
    gptscript = GPTScript()
    tools = await gptscript.parse_tool("Instructions: Say hello!")
    print(tools)
    gptscript.close()
```

### `fmt()`

Parse convert a tool data structure into a GPTScript file.

```python
from gptscript.gptscript import GPTScript


async def fmt_example():
    gptscript = GPTScript()
    tools = await gptscript.parse_tool("Instructions: Say hello!")
    print(tools)

    contents = gptscript.fmt(tools)
    print(contents)  # This would print "Instructions: Say hello!"
    gptscript.close()
```

### `evaluate()`

Executes a tool with optional arguments.

```python
from gptscript.gptscript import GPTScript
from gptscript.tool import ToolDef


async def evaluate_example():
    tool = ToolDef(instructions="Who was the president of the United States in 1928?")
    gptscript = GPTScript()

    run = gptscript.evaluate(tool)
    output = await run.text()

    print(output)

    gptscript.close()
```

### `run()`

Executes a GPT script file with optional input and arguments. The script is relative to the callers source directory.

```python
from gptscript.gptscript import GPTScript


async def evaluate_example():
    gptscript = GPTScript()

    run = gptscript.run("/path/to/file")
    output = await run.text()

    print(output)

    gptscript.close()
```

### Streaming events

GPTScript provides events for the various steps it takes. You can get those events and process them
with `event_handlers`. The `evaluate` method is used here, but the same functionality exists for the `run` method.

```python
from gptscript.gptscript import GPTScript
from gptscript.frame import RunFrame, CallFrame, PromptFrame
from gptscript.run import Run


async def process_event(run: Run, event: RunFrame | CallFrame | PromptFrame):
    print(event.__dict__)


async def evaluate_example():
    gptscript = GPTScript()

    run = gptscript.run("/path/to/file", event_handlers=[process_event])
    output = await run.text()

    print(output)

    gptscript.close()
```

### Confirm

Using the `confirm: true` option allows a user to inspect potentially dangerous commands before they are run. The caller
has the ability to allow or disallow their running. In order to do this, a caller should look for the `CallConfirm`
event.

```python
from gptscript.gptscript import GPTScript
from gptscript.frame import RunFrame, CallFrame, PromptFrame
from gptscript.run import Run, RunEventType
from gptscript.confirm import AuthResponse

gptscript = GPTScript()


async def confirm(run: Run, event: RunFrame | CallFrame | PromptFrame):
    if event.type == RunEventType.callConfirm:
        # AuthResponse also has a "message" field to specify why the confirm was denied.
        await gptscript.confirm(AuthResponse(accept=True))


async def evaluate_example():
    run = gptscript.run("/path/to/file", event_handlers=[confirm])
    output = await run.text()

    print(output)

    gptscript.close()
```

### Prompt

Using the `prompt: true` option allows a script to prompt a user for input. In order to do this, a caller should look
for the `Prompt` event. Note that if a `Prompt` event occurs when it has not explicitly been allowed, then the run will
error.

```python
from gptscript.gptscript import GPTScript
from gptscript.frame import RunFrame, CallFrame, PromptFrame
from gptscript.run import Run
from gptscript.opts import Options
from gptscript.prompt import PromptResponse

gptscript = GPTScript()


async def prompt(run: Run, event: RunFrame | CallFrame | PromptFrame):
    if isinstance(event, PromptFrame):
        # The responses field here is a dictionary of prompt fields to values.
        await gptscript.prompt(PromptResponse(id=event.id, responses={event.fields[0]: "Some value"}))


async def evaluate_example():
    run = gptscript.run("/path/to/file", opts=Options(prompt=True), event_handlers=[prompt])
    output = await run.text()

    print(output)

    gptscript.close()
```

## Example Usage

```python
from gptscript.gptscript import GPTScript
from gptscript.tool import ToolDef

# Create the GPTScript object
gptscript = GPTScript()

# Define a tool
complex_tool = ToolDef(
    tools=["sys.write"],
    jsonResponse=True,
    cache=False,
    instructions="""
    Create three short graphic artist descriptions and their muses.
    These should be descriptive and explain their point of view.
    Also come up with a made-up name, they each should be from different
    backgrounds and approach art differently.
    the JSON response format should be:
    {
        artists: [{
            name: "name"
            description: "description"
        }]
    }
    """
)

# Execute the complex tool
run = gptscript.evaluate(complex_tool)
print(await run.text())

gptscript.close()
```

### Example 2 multiple tools

In this example, multiple tool are provided to the exec function. The first tool is the only one that can exclude the
name field. These will be joined and passed into the gptscript as a single gptscript.

```python
from gptscript.gptscript import GPTScript
from gptscript.tool import ToolDef

gptscript = GPTScript()

tools = [
    ToolDef(tools=["echo"], instructions="echo hello times"),
    ToolDef(
        name="echo",
        tools=["sys.exec"],
        description="Echo's the input",
        args={"input": "the string input to echo"},
        instructions="""
        #!/bin/bash
        echo ${input}
        """,
    ),
]

run = gptscript.evaluate(tools)

print(await run.text())

gptscript.close()
```

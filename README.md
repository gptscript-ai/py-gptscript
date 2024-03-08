# GPTScript Python Module

## Introduction

The GPTScript Python module is a library that provides a simple interface to create and run gptscripts within Python applications, and Jupyter notebooks. It allows you to define tools, execute them, and process the responses.

## Installation

You can install the GPTScript Python module using pip.

```bash
pip install gptscript
```

On MacOS, Windows X6

### SDIST and none-any wheel installations

When installing from the sdist or the none-any wheel, the binary is not packaged by default. You must run the install_gptscript command to install the binary.

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

## Using the Module

The module requires the OPENAI_API_KEY environment variable to be set with your OPENAI key. You can set it in your shell or in your code.

```bash
export OPENAI_AI_KEY="your-key"
```

## Tools

The `Tool` class represents a gptscript tool. The fields align with what you would be able to define in a normal gptscript .gpt file.

### Fields

- `name`: The name of the tool.
- `description`: A description of the tool.
- `tools`: Additional tools associated with the main tool.
- `max_tokens`: The maximum number of tokens to generate.
- `model`: The GPT model to use.
- `cache`: Whether to use caching for responses.
- `temperature`: The temperature parameter for response generation.
- `args`: Additional arguments for the tool.
- `internal_prompt`: Internal prompt for the tool.
- `instructions`: Instructions or additional information about the tool.
- `json_response`: Whether the response should be in JSON format.(If you set this to True, you must say 'json' in the instructions as well.)

## Primary Functions

Aside from the list methods there are `exec` and `exec_file` methods that allow you to execute a tool and get the responses. Those functions also provide a streaming version of execution if you want to process the output streams in your code as the tool is running.

### Opts

You can pass the following options to the exec and exec_file functions:

opts= {
    "cache": True(default)|False,
    "cache-dir": "",
}

Cache can be set to true or false to enable or disable caching globally or it can be set at the individual tool level. The cache-dir can be set to a directory to use for caching. If not set, the default cache directory will be used.

### `list_models()`

This function lists the available GPT models.

```python
from gptscript.command import list_models

models = list_models()
print(models)
```

### `list_tools()`

This function lists the available tools.

```python
from gptscript.command import list_tools

tools = list_tools()
print(tools)
```

### `exec(tool, opts)`

This function executes a tool and returns the response.

```python
from gptscript.command import exec
from gptscript.tool import Tool

tool = Tool(
    json_response=True,
    instructions="""
Create three short graphic artist descriptions and their muses. 
These should be descriptive and explain their point of view.
Also come up with a made up name, they each should be from different
backgrounds and approach art differently.
the response should be in JSON and match the format:
{
   artists: [{
      name: "name"
      description: "description"
   }]
}
""",
    )


response = exec(tool)
print(response)
```

### `exec_file(tool_path, input="", opts)`

This function executes a tool from a file and returns the response. The input values are passed to the tool as args.

```python
from gptscript.command import exec_file

response = exec_file("./example.gpt")
print(response)
```

### `stream_exec(tool, opts)`

This function streams the execution of a tool and returns the output, error, and process wait function. The streams must be read from.

```python
from gptscript.command import stream_exec
from gptscript.tool import Tool

tool = Tool(
    json_response=True,
    instructions="""
Create three short graphic artist descriptions and their muses. 
These should be descriptive and explain their point of view.
Also come up with a made up name, they each should be from different
backgrounds and approach art differently.
the response should be in JSON and match the format:
{
   artists: [{
      name: "name"
      description: "description"
   }]
}
""",
    )

def print_output(out, err):
    # Error stream has the debug info that is useful to see
    for line in err:
        print(line)

    for line in out:
        print(line)

out, err, wait = stream_exec(tool)
print_output(out, err)
wait()
```

### `stream_exec_file(tool_path, input="",opts)`

This function streams the execution of a tool from a file and returns the output, error, and process wait function. The input values are passed to the tool as args.

```python
from gptscript.command import stream_exec_file

def print_output(out, err):
    # Error stream has the debug info that is useful to see
    for line in err:
        print(line)

    for line in out:
        print(line)

out, err, wait = stream_exec_file("./init.gpt")
print_output(out, err)
wait()
```

## Example Usage

```python
from gptscript.command import exec
from gptscript.tool import FreeForm, Tool

# Define a simple tool
simple_tool = FreeForm(
    content="""
What is the capital of the United States?
"""
)

# Define a complex tool
complex_tool = Tool(
    tools=["sys.write"],
    json_response=True,
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
response, err = exec(complex_tool)
print(err)
print(response)

# Execute the simple tool
resp, err = exec(simple_tool)
print(err)
print(resp)
```

### Example 2 multiple tools

In this example, multiple tool are provided to the exec function. The first tool is the only one that can exclude the name field. These will be joined and passed into the gptscript as a single gpt script.

```python
from gptscript.command import exec
from gptscript.tool import Tool

tools = [
    Tool(tools=["echo"], instructions="echo hello times"),
    Tool(
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

resp, err = exec(tools)
print(err)
print(resp)
```

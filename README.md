# GPTScript Python Module

## Introduction

The GPTScript Python module is a library that provides a simple interface to create and run gptscripts within Python applications, and Jupyter notebooks. It allows you to define tools, execute them, and process the responses.

## Installation

You can install the GPTScript Python module using pip.

```bash
pip install gptscript
```

You will also want to have the tool download and install the gptscript cli by running:

```bash
install_gptscript
```

The script is added to the same bin directory as the python executable, so it should be in your path.

Or you can install the gptscript cli from your code by running:

```python
from gptscript.install import install
install()
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

### `exec(tool)`

This function executes a tool and returns the response.

```python
from gptscript.command import exec, complex_tool

response = exec(complex_tool())
print(response)
```

### `exec_file(tool_path)`

This function executes a tool from a file and returns the response.

```python
from gptscript.command import exec_file

response = exec_file("./init.gpt")
print(response)
```

### `stream_exec(tool)`

This function streams the execution of a tool and returns the output, error, and process wait function.

```python
from gptscript.command import stream_exec, complex_tool

out, err, wait = stream_exec(complex_tool())
print(out)
print(err)
wait()
```

### `stream_exec_file(tool_path)`

This function streams the execution of a tool from a file and returns the output, error, and process wait function.

```python
from gptscript.command import stream_exec_file

out, err, wait = stream_exec_file("./init.gpt")
print(out)
print(err)
wait()
```

## Example Usage

```python
from gptscript.tool import Tool

# Define a simple tool
simple_tool = Tool(
    instructions="""
    This tool is used to generate a simple prompt
    """
)

# Define a complex tool
complex_tool = Tool(
    tools="sys.write",
    json_response=True,
    cache=False,
    instructions="""
    Create three short graphic artist descriptions and their muses.
    These should be descriptive and explain their point of view.
    Also come up with a made-up name, they each should be from different
    backgrounds and approach art differently.
    the response format should be:
    {
        artists: [{
            name: "name"
            description: "description"
        }]
    }
    """
)

# Execute the complex tool
response = exec(complex_tool)
print(response)
```

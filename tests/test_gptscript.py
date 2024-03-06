import os
import pytest
from gptscript.command import (
    list_models,
    list_tools,
    exec,
    exec_file,
    stream_exec,
    stream_exec_file,
)
from gptscript.tool import Tool, FreeForm


# Ensure the OPENAI_API_KEY is set for testing
@pytest.fixture(scope="session", autouse=True)
def check_api_key():
    if os.getenv("OPENAI_API_KEY") is None:
        pytest.fail("OPENAI_API_KEY not set", pytrace=False)


# Simple tool for testing
@pytest.fixture
def simple_tool():
    return FreeForm(
        content="""
What is the capital of the united states?
"""
    )


# Complex tool for testing
@pytest.fixture
def complex_tool():
    return Tool(
        tools=["sys.write"],
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


# Fixture for a list of tools
@pytest.fixture
def tool_list():
    return [
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


# Test function for listing models
def test_list_models():
    models = list_models()
    assert isinstance(models, list), "Expected list_models to return a list"


# Test function for listing tools
def test_list_tools():
    out = list_tools()
    assert out is not None, "Expected some output from list_tools"


# Test execution of a simple tool
def test_exec_simple_tool(simple_tool):
    out, err = exec(simple_tool)
    assert out is not None, "Expected some output from exec using simple_tool"


# Test execution of a complex tool
def test_exec_complex_tool(complex_tool):
    out, err = exec(complex_tool)
    assert out is not None, "Expected some output from exec using complex_tool"


# Test execution with a list of tools
def test_exec_tool_list(tool_list):
    out, err = exec(tool_list)
    assert out is not None, "Expected some output from exec using a list of tools"


# Test streaming execution of a complex tool
def test_stream_exec_complex_tool(complex_tool):
    out, err, wait = stream_exec(complex_tool)
    resp = wait()  # Wait for streaming to complete
    assert (
        out is not None or err is not None
    ), "Expected some output or error from stream_exec using complex_tool"
    assert (
        resp == 0
    ), "Expected a successful response from stream_exec using complex_tool"


# Test streaming execution from a file
def test_stream_exec_file():
    out, err, wait = stream_exec_file("./fixtures/test.gpt")
    resp = wait()  # Wait for streaming to complete
    assert (
        out is not None or err is not None
    ), "Expected some output or error from stream_exec_file"
    assert resp == 0, "Expected a successful response from stream_exec_file"

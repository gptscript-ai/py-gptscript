import os

import pytest

from gptscript.command import (
    version,
    list_models,
    list_tools,
    exec,
    exec_file,
    stream_exec,
    stream_exec_with_events,
    stream_exec_file,
    stream_exec_file_with_events,
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
        Tool(tools=["echo"], instructions="echo hello there"),
        Tool(name="other", tools=["echo"], instructions="echo hello somewhere else"),
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


def test_version():
    v = version()
    assert "gptscript version " in v


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
    opts = {"cache": False}
    out, err = exec(complex_tool, opts=opts)
    assert out is not None, "Expected some output from exec using complex_tool"


# Test execution with a list of tools
def test_exec_tool_list(tool_list):
    out, err = exec(tool_list)
    assert out.strip() == "hello there", "Unexpected output from exec using a list of tools"


def test_exec_tool_list_with_sub_tool(tool_list):
    out, err = exec(tool_list, opts={"subTool": "other"})
    assert out.strip() == "hello somewhere else", "Unexpected output from exec using a list of tools with sub tool"


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


def test_exec_file_with_chdir():
    # By changing the directory here, we should be able to find the test.gpt file without `./tests`
    out, err = exec_file("./test.gpt", opts={"chdir": "./tests/fixtures"})
    for line in out:
        print(line)
    for line in err:
        print(line)
    assert (
            out is not None and err is not None
    ), "Expected some output or error from stream_exec_file"


# Test streaming execution from a file
def test_stream_exec_file():
    out, err, wait = stream_exec_file("./tests/fixtures/test.gpt")
    resp = wait()  # Wait for streaming to complete
    for line in out:
        print(line)
    for line in err:
        print(line)
    assert (
            out is not None or err is not None
    ), "Expected some output or error from stream_exec_file"
    assert resp == 0, "Expected a successful response from stream_exec_file"


def test_stream_exec_tool_with_events(simple_tool):
    out, err, events, wait = stream_exec_with_events(simple_tool)
    has_events = False
    for line in events:
        has_events = line != ""

    assert has_events, "Expected some events from stream_exec_with_events"
    resp = wait()  # Wait for streaming to complete
    assert (
            out is not None or err is not None
    ), "Expected some output or error from stream_exec_file"
    assert resp == 0, "Expected a successful response from stream_exec_file"


def test_stream_exec_file_with_events():
    out, err, events, wait = stream_exec_file_with_events("./tests/fixtures/test.gpt")
    has_events = False
    for line in events:
        has_events = line != ""

    assert has_events, "Expected some events from stream_exec_file_with_events"
    resp = wait()  # Wait for streaming to complete
    assert (
            out is not None or err is not None
    ), "Expected some output or error from stream_exec_file"
    assert resp == 0, "Expected a successful response from stream_exec_file"

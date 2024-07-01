import os
import platform
import subprocess

import pytest

from gptscript.confirm import AuthResponse
from gptscript.frame import RunEventType, CallFrame, RunFrame, RunState, PromptFrame
from gptscript.gptscript import GPTScript
from gptscript.install import install, gptscript_binary_name, python_bin_dir
from gptscript.opts import GlobalOptions, Options
from gptscript.prompt import PromptResponse
from gptscript.run import Run
from gptscript.text import Text
from gptscript.tool import ToolDef, ArgumentSchema, Property, Tool


# Ensure the OPENAI_API_KEY is set for testing
@pytest.fixture(scope="session", autouse=True)
def gptscript():
    if os.getenv("OPENAI_API_KEY") is None:
        pytest.fail("OPENAI_API_KEY not set", pytrace=False)
    try:
        gptscript = GPTScript(GlobalOptions(apiKey=os.getenv("OPENAI_API_KEY")))
        yield gptscript
        gptscript.close()
    except Exception as e:
        pytest.fail(e, pytrace=False)


# Simple tool for testing
@pytest.fixture
def simple_tool():
    return ToolDef(
        instructions="What is the capital of the united states?"
    )


# Complex tool for testing
@pytest.fixture
def complex_tool():
    return ToolDef(
        tools=["sys.write"],
        jsonResponse=True,
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
    shebang = "#!/bin/bash"
    if platform.system() == "windows":
        shebang = "#!/usr/bin/env powershell.exe"
    return [
        ToolDef(tools=["echo"], instructions="echo 'hello there'"),
        ToolDef(name="other", tools=["echo"], instructions="echo 'hello somewhere else'"),
        ToolDef(
            name="echo",
            tools=["sys.exec"],
            description="Echoes the input",
            arguments=ArgumentSchema(properties={"input": Property("The string input to echo")}),
            instructions=f"""
${shebang}
echo ${input}
""",
        ),
    ]


def test_install():
    install()
    bin_name = str(python_bin_dir / gptscript_binary_name)
    process = subprocess.Popen([bin_name, '-v'], stdout=subprocess.PIPE, text=True)
    assert process.stdout.read().startswith('gptscript version ')


@pytest.mark.asyncio
async def test_create_another_gptscript():
    g = GPTScript()
    version = await g.version()
    g.close()
    assert "gptscript version" in version


@pytest.mark.asyncio
async def test_version(gptscript):
    v = await gptscript.version()
    assert "gptscript version " in v


@pytest.mark.asyncio
async def test_list_models(gptscript):
    models = await gptscript.list_models()
    assert isinstance(models, list) and len(models) > 1, "Expected list_models to return a list"


@pytest.mark.asyncio
async def test_list_tools(gptscript):
    out = await gptscript.list_tools()
    assert out is not None, "Expected some output from list_tools"


@pytest.mark.asyncio
async def test_abort_run(gptscript):
    async def about_run(run: Run, e: CallFrame | RunFrame | PromptFrame):
        await run.aclose()

    run = gptscript.evaluate(ToolDef(instructions="What is the capital of the united states?"),
                             Options(disableCache=True), event_handlers=[about_run])

    assert "Run was aborted" in await run.text(), "Unexpected output from abort_run"
    assert RunState.Error == run.state(), "Unexpected run state after aborting"


@pytest.mark.asyncio
async def test_eval_simple_tool(gptscript, simple_tool):
    run = gptscript.evaluate(simple_tool)
    out = await run.text()
    assert "Washington" in out, "Unexpected response for tool run"


@pytest.mark.asyncio
async def test_eval_complex_tool(gptscript, complex_tool):
    run = gptscript.evaluate(complex_tool, Options(disableCache=True))
    out = await run.text()
    assert '"artists":' in out, "Expected some output from eval using complex_tool"


@pytest.mark.asyncio
async def test_eval_tool_list(gptscript, tool_list):
    run = gptscript.evaluate(tool_list)
    out = await run.text()
    assert out.strip() == "hello there", "Unexpected output from eval using a list of tools"


@pytest.mark.asyncio
async def test_eval_tool_list_with_sub_tool(gptscript, tool_list):
    run = gptscript.evaluate(tool_list, opts=Options(subTool="other"))
    out = await run.text()
    assert out.strip() == "hello somewhere else", "Unexpected output from eval using a list of tools with sub tool"


@pytest.mark.asyncio
async def test_stream_exec_complex_tool(gptscript, complex_tool):
    stream_output = ""

    async def collect_events(run: Run, e: CallFrame | RunFrame | PromptFrame):
        nonlocal stream_output
        if str(e.type.name).startswith("call") and e.output is not None:
            for output in e.output:
                stream_output += output.content

    run = gptscript.evaluate(complex_tool, Options(disableCache=True), event_handlers=[collect_events])
    out = await run.text()
    assert '"artists":' in out, "Expected some output from streaming using complex_tool"
    assert '"artists":' in stream_output, "Expected stream_output to have output"


@pytest.mark.asyncio
async def test_stream_run_file(gptscript):
    stream_output = ""

    async def collect_events(run: Run, e: CallFrame | RunFrame | PromptFrame):
        nonlocal stream_output
        if str(e.type.name).startswith("call") and e.output is not None:
            for output in e.output:
                stream_output += output.content

    run = gptscript.run("./tests/fixtures/test.gpt", Options(disableCache=True), event_handlers=[collect_events])
    assert "Ronald Reagan" in await run.text(), "Expect streaming file to have correct output"
    assert "Ronald Reagan" in stream_output, "Expect stream_output to have correct output when streaming from file"

@pytest.mark.asyncio
async def test_credential_override(gptscript):
    run = gptscript.run(
        os.getcwd() + "/tests/fixtures/credential-override.gpt",
        Options(
            disableCache=True,
            credentialOverrides=['test.ts.credential_override:TEST_CRED=foo']
        ),
    )
    assert "foo" in await run.text(), "Expect credential override to have correct output"

@pytest.mark.asyncio
async def test_eval_with_context(gptscript):
    wd = os.getcwd()
    tool = ToolDef(
        instructions="What is the capital of the united states?",
        context=[wd + "/tests/fixtures/acorn-labs-context.gpt"],
    )

    run = gptscript.evaluate(tool)

    assert "Acorn Labs" == await run.text(), "Unexpected output from eval using context"


@pytest.mark.asyncio
async def test_parse_simple_file(gptscript):
    wd = os.getcwd()
    tools = await gptscript.parse(wd + "/tests/fixtures/test.gpt")
    assert len(tools) == 1, "Unexpected number of tools for parsing simple file"
    assert isinstance(tools[0], Tool), "Unexpected node type from parsing simple file"
    assert tools[0].instructions == "Who was the president of the United States in 1986?", \
        "Unexpected output from parsing simple file"


@pytest.mark.asyncio
async def test_parse_tool(gptscript):
    tools = await gptscript.parse_tool("echo hello")
    assert len(tools) == 1, "Unexpected number of tools for parsing tool"
    assert isinstance(tools[0], Tool), "Unexpected node type from parsing tool"
    assert tools[0].instructions == "echo hello", "Unexpected output from parsing tool"


@pytest.mark.asyncio
async def test_parse_tool_with_text_node(gptscript):
    tools = await gptscript.parse_tool("echo hello\n---\n!markdown\nhello")
    assert len(tools) == 2, "Unexpected number of tools for parsing tool with text node"
    assert isinstance(tools[0], Tool), "Unexpected node type for first tool from parsing tool with text node"
    assert isinstance(tools[1], Text), "Unexpected node type for second tool from parsing tool with text node"
    assert tools[0].instructions == "echo hello", "Unexpected instructions from parsing tool with text node"
    assert tools[1].text == "hello", "Unexpected text node text from parsing tool with text node"
    assert tools[1].format == "markdown", "Unexpected text node fmt from parsing tool with text node"


@pytest.mark.asyncio
async def test_fmt(gptscript):
    nodes = [
        Tool(tools=["echo"], instructions="echo hello there"),
        Tool(
            name="echo",
            instructions="#!/bin/bash\necho hello there",
            arguments=ArgumentSchema(
                properties={"input": Property(description="The string input to echo")},
            )
        )
    ]

    expected_output = """Tools: echo

echo hello there

---
Name: echo
Parameter: input: The string input to echo

#!/bin/bash
echo hello there
"""
    assert await gptscript.fmt(nodes) == expected_output, "Unexpected output from fmt using nodes"


@pytest.mark.asyncio
async def test_fmt_with_text_node(gptscript):
    nodes = [
        Tool(tools=["echo"], instructions="echo hello there"),
        Text(fmt="markdown", text="We now echo hello there"),
        Tool(
            name="echo",
            instructions="#!/bin/bash\necho hello there",
            arguments=ArgumentSchema(
                properties={"input": Property(description="The string input to echo")},
            )
        )
    ]

    expected_output = """Tools: echo

echo hello there

---
!markdown
We now echo hello there
---
Name: echo
Parameter: input: The string input to echo

#!/bin/bash
echo hello there
"""

    assert await gptscript.fmt(nodes) == expected_output, "Unexpected output from fmt using nodes"


@pytest.mark.asyncio
async def test_tool_chat(gptscript):
    tool = ToolDef(
        chat=True,
        instructions="You are a chat bot. Don't finish the conversation until I say 'bye'.",
        tools=["sys.chat.finish"],
    )

    inputs = [
        "List the three largest states in the United States by area.",
        "What is the capital of the third one?",
        "What timezone is the first one in?",
    ]
    expected_outputs = [
        "California",
        "Sacramento",
        "Alaska Time Zone",
    ]

    run = gptscript.evaluate(tool)
    await run.text()
    assert run.state() == RunState.Continue, "first run in unexpected state"

    for i in range(len(inputs)):
        run = run.next_chat(inputs[i])

        output = await run.text()
        assert run.state() == RunState.Continue, "run in unexpected state"
        assert expected_outputs[i] in output, "unexpected output for chat"


@pytest.mark.asyncio
async def test_file_chat(gptscript):
    inputs = [
        "List the 3 largest of the Great Lakes by volume.",
        "What is the volume of the second one in cubic miles?",
        "What is the total area of the third one in square miles?",
    ]
    expected_outputs = [
        "Lake Superior",
        "Lake Michigan",
        "Lake Huron",
    ]

    run = gptscript.run(os.getcwd() + "/tests/fixtures/chat.gpt")
    await run.text()
    assert run.state() == RunState.Continue, "first run in unexpected state"

    for i in range(len(inputs)):
        run = run.next_chat(inputs[i])

        output = await run.text()
        assert run.state() == RunState.Continue, "run in unexpected state"
        assert expected_outputs[i] in output, "unexpected output for chat"


@pytest.mark.asyncio
async def test_global_tools(gptscript):
    run_start_seen = False
    call_start_seen = False
    call_progress_seen = False
    call_finish_seen = False
    run_finish_seen = False
    event_output = ""

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal run_start_seen, call_start_seen, call_progress_seen, call_finish_seen, run_finish_seen, event_output
        if isinstance(frame, RunFrame):
            if frame.type == RunEventType.runStart:
                run_start_seen = True
            elif frame.type == RunEventType.runFinish:
                run_finish_seen = True
        else:
            if frame.type == RunEventType.callStart:
                call_start_seen = True
            elif frame.type == RunEventType.callProgress:
                call_progress_seen = True
                for output in frame.output:
                    event_output += output.content
            elif frame.type == RunEventType.callFinish:
                call_finish_seen = True

    run = gptscript.run(os.getcwd() + "/tests/fixtures/global-tools.gpt",
                        Options(disableCache=True),
                        event_handlers=[process_event],
                        )

    assert "Hello!" in await run.text(), "Unexpected output from global tool test"
    assert "Hello" in event_output, "Unexpected stream output from global tool test"

    assert run_start_seen and call_start_seen and call_progress_seen and call_finish_seen and run_finish_seen, \
        f"One of these is False: {run_start_seen}, {call_start_seen}, {call_progress_seen}, {call_finish_seen}, {run_finish_seen}"


@pytest.mark.asyncio
async def test_confirm(gptscript):
    confirm_event_found = False
    event_content = ""

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal confirm_event_found, event_content
        if frame.type == RunEventType.callConfirm:
            confirm_event_found = True
            assert '"ls' in frame.input or '"dir' in frame.input, "Unexpected confirm input: " + frame.input
            await gptscript.confirm(AuthResponse(frame.id, True))
        elif frame.type == RunEventType.callProgress:
            for output in frame.output:
                event_content += output.content

    tool = ToolDef(tools=["sys.exec"], instructions="List the files in the current directory as '.'.")
    out = await gptscript.evaluate(tool,
                                   Options(confirm=True, disableCache=True),
                                   event_handlers=[process_event],
                                   ).text()

    assert confirm_event_found, "No confirm event"
    # Running the `dir` command in Windows will give the contents of the tests directory
    # while running `ls` on linux will give the contents of the repo directory.
    assert (
                   "README.md" in out and "requirements.txt" in out
           ) or (
                   "fixtures" in out and "test_gptscript.py" in out
           ), "Unexpected output: " + out
    assert (
                   "README.md" in event_content and "requirements.txt" in event_content
           ) or (
                   "fixtures" in event_content and "test_gptscript.py" in event_content
           ), "Unexpected event output: " + event_content


@pytest.mark.asyncio
async def test_confirm_deny(gptscript):
    confirm_event_found = False
    event_content = ""

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal confirm_event_found, event_content
        if frame.type == RunEventType.callConfirm:
            confirm_event_found = True
            assert '"ls"' in frame.input, "Unexpected confirm input: " + frame.input
            await gptscript.confirm(AuthResponse(frame.id, False, "I will not allow it!"))
        elif frame.type == RunEventType.callProgress:
            for output in frame.output:
                event_content += output.content

    tool = ToolDef(tools=["sys.exec"],
                   instructions="List the files in the current directory as '.'. If that doesn't work"
                                "print the word FAIL.")
    out = await gptscript.evaluate(tool,
                                   Options(confirm=True, disableCache=True),
                                   event_handlers=[process_event],
                                   ).text()

    assert confirm_event_found, "No confirm event"
    assert "FAIL" in out, "Unexpected output: " + out
    assert "FAIL" in event_content, "Unexpected event output: " + event_content


@pytest.mark.asyncio
async def test_prompt(gptscript):
    prompt_event_found = False
    event_content = ""

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal prompt_event_found, event_content
        if frame.type == RunEventType.prompt:
            prompt_event_found = True
            assert len(frame.fields) == 1, "Unexpected number of fields: " + str(frame.fields)
            assert "first name" in frame.fields[0], "Unexpected field: " + frame.fields[0]
            await gptscript.prompt(PromptResponse(frame.id, {frame.fields[0]: "Clicky"}))
        elif frame.type == RunEventType.callProgress:
            for output in frame.output:
                event_content += output.content

    tool = ToolDef(
        tools=["sys.prompt"],
        instructions="Use the sys.prompt user to ask the user for 'first name' which is not sensitive. After you get their first name, say hello.",
    )
    out = await gptscript.evaluate(
        tool,
        Options(prompt=True, disableCache=True),
        event_handlers=[process_event],
    ).text()

    assert prompt_event_found, "No prompt event"
    assert "Clicky" in out, "Unexpected output: " + out
    assert "Clicky" in event_content, "Unexpected event output: " + event_content


@pytest.mark.asyncio
async def test_prompt_without_prompt_allowed(gptscript):
    prompt_event_found = False

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal prompt_event_found
        if frame.type == RunEventType.prompt:
            prompt_event_found = True
            assert len(frame.fields) == 1, "Unexpected number of fields: " + str(frame.fields)
            assert "first name" in frame.fields[0], "Unexpected field: " + frame.fields[0]
            await gptscript.prompt(PromptResponse(frame.id, {frame.fields[0]: "Clicky"}))

    tool = ToolDef(
        tools=["sys.prompt"],
        instructions="Use the sys.prompt user to ask the user for 'first name' which is not sensitive. After you get their first name, say hello.",
    )
    run = gptscript.evaluate(
        tool,
        event_handlers=[process_event],
    )

    out = await run.text()

    assert not prompt_event_found, "Prompt event occurred"
    assert "prompt event occurred" in out, "Unexpected output: " + out

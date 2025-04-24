import base64
import gzip
import json
import os
import platform
import subprocess
from datetime import datetime, timedelta, timezone
from time import sleep

import pytest

from gptscript.confirm import AuthResponse
from gptscript.credentials import Credential
from gptscript.datasets import DatasetElement
from gptscript.exec_utils import get_env
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
        # Start an initial GPTScript instance.
        # This one doesn't have any options, but it's there to ensure that using another instance works as expected in all cases.
        g_first = GPTScript()
        gptscript = GPTScript(GlobalOptions(apiKey=os.getenv("OPENAI_API_KEY")))
        yield gptscript
        gptscript.close()
        g_first.close()
    except Exception as e:
        pytest.fail(e, pytrace=False)


# Simple tool for testing
@pytest.fixture(scope="function")
def simple_tool():
    return ToolDef(
        instructions="What is the capital of the united states?"
    )


# Complex tool for testing
@pytest.fixture(scope="function")
def complex_tool():
    return ToolDef(
        jsonResponse=True,
        instructions="""Create three short graphic artist descriptions and their muses.
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
@pytest.fixture(scope="function")
def tool_list():
    shebang = "#!/bin/bash"
    if platform.system().lower() == "windows":
        shebang = "#!/usr/bin/env powershell.exe"
    return [
        ToolDef(tools=["echo"], instructions="echo 'hello there'"),
        ToolDef(name="other", tools=["echo"], instructions="echo 'hello somewhere else'"),
        ToolDef(
            name="echo",
            tools=["sys.exec"],
            description="Echoes the input",
            arguments=ArgumentSchema(properties={"input": Property(description="The string input to echo")}),
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
@pytest.mark.skipif(os.environ.get("ANTHROPIC_API_KEY") is None, reason="ANTHROPIC_API_KEY not set")
async def test_list_models_from_provider(gptscript):
    models = await gptscript.list_models(
        providers=["github.com/gptscript-ai/claude3-anthropic-provider"],
        credential_overrides=["github.com/gptscript-ai/claude3-anthropic-provider/credential:ANTHROPIC_API_KEY"],
    )
    assert isinstance(models, list) and len(models) > 1, "Expected list_models to return a list"
    for model in models:
        assert model.id.startswith("claude-3-"), "Unexpected model name"
        assert model.id.endswith("from github.com/gptscript-ai/claude3-anthropic-provider"), "Unexpected model name"


@pytest.mark.asyncio
@pytest.mark.skipif(os.environ.get("ANTHROPIC_API_KEY") is None, reason="ANTHROPIC_API_KEY not set")
async def test_list_models_from_default_provider():
    g = GPTScript(GlobalOptions(defaultModelProvider="github.com/gptscript-ai/claude3-anthropic-provider"))
    try:
        models = await g.list_models(
            credential_overrides=["github.com/gptscript-ai/claude3-anthropic-provider/credential:ANTHROPIC_API_KEY"],
        )
        assert isinstance(models, list) and len(models) > 1, "Expected list_models to return a list"
        for model in models:
            assert model.id.startswith("claude-3-"), "Unexpected model name"
            assert model.id.endswith("from github.com/gptscript-ai/claude3-anthropic-provider"), "Unexpected model name"
    finally:
        g.close()


@pytest.mark.asyncio
async def test_abort_run(gptscript):
    async def abort_run(run: Run, e: CallFrame | RunFrame | PromptFrame):
        await run.aclose()

    run = gptscript.evaluate(ToolDef(instructions="What is the capital of the united states?"),
                             Options(disableCache=True), event_handlers=[abort_run])
    try:
        await run.text()
    except Exception as e:
        assert "Run was aborted" in str(e), "Unexpected output from abort_run"

    assert RunState.Error == run.state(), "Unexpected run state after aborting"


@pytest.mark.asyncio
async def test_restart_failed_run(gptscript):
    shebang = "#!/bin/bash"
    instructions = f"""{shebang}
exit ${{EXIT_CODE}}
"""
    if platform.system().lower() == "windows":
        shebang = "#!/usr/bin/env powershell.exe"
        instructions = f"""{shebang}
exit $env:EXIT_CODE
"""
    tools = [
        ToolDef(tools=["my-context"]),
        ToolDef(
            name="my-context",
            type="context",
            instructions=instructions,
        ),
    ]

    run = gptscript.evaluate(tools, Options(disableCache=True, env=["EXIT_CODE=1"]))

    try:
        await run.text()
        assert False, "Expected run to fail"
    except:
        pass

    assert run.state() == RunState.Error, "Unexpected run state after exit 1"

    run.opts.env = None

    run = run.next_chat("")
    await run.text()

    assert run.state() != RunState.Error, "Unexpected run state after restart"


@pytest.mark.asyncio
async def test_eval_simple_tool(gptscript, simple_tool):
    run = gptscript.evaluate(simple_tool, Options(disableCache=True))
    out = await run.text()
    prompt_tokens, completion_tokens, total_tokens = 0, 0, 0
    for c in run.calls().values():
        prompt_tokens += c.usage.promptTokens
        completion_tokens += c.usage.completionTokens
        total_tokens += c.usage.totalTokens

    assert "Washington" in out, "Unexpected response for tool run"
    assert prompt_tokens > 0, "Unexpected promptTokens for tool run"
    assert completion_tokens > 0, "Unexpected completionTokens for tool run"
    assert total_tokens > 0, "Unexpected totalTokens for tool run"


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

    # In this case, we expect the total number of toolResults to be 1 or 2 depending on what the LLM tries to do.
    total_tool_results = 0
    for c in run.calls().values():
        total_tool_results += c.toolResults

    assert total_tool_results >= 1, "Unexpected number of toolResults"


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
async def test_simple_run_file(gptscript):
    cwd = os.getcwd().removesuffix("/tests")
    run = gptscript.run(cwd + "/tests/fixtures/test.gpt")
    out = await run.text()
    assert "Ronald Reagan" in out, "Expect run file to have correct output"

    # Run again and make sure the output is the same, and the cache is used
    run = gptscript.run(cwd + "/tests/fixtures/test.gpt")
    second_out = await run.text()
    assert second_out == out, "Expect run file to have same output as previous run"

    # In this case, we expect one cached call frame
    for c in run.calls().values():
        assert c.chatResponseCached, "Expect chatResponseCached to be true"


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
    gptscriptFile = "credential-override.gpt"
    if platform.system().lower() == "windows":
        gptscriptFile = "credential-override-windows.gpt"
    run = gptscript.run(
        f"{os.getcwd()}{os.sep}tests{os.sep}fixtures{os.sep}{gptscriptFile}",
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
        tools=[wd + "/tests/fixtures/acorn-labs-context.gpt"],
    )

    run = gptscript.evaluate(tool)
    assert "Acorn Labs" == await run.text(), "Unexpected output from eval using context"


@pytest.mark.asyncio
async def test_load_simple_file(gptscript):
    wd = os.getcwd()
    prg = await gptscript.load_file(wd + "/tests/fixtures/test.gpt")
    assert prg.toolSet[prg.entryToolId].instructions == "Who was the president of the United States in 1986?", \
        "Unexpected output from parsing simple file"


@pytest.mark.asyncio
async def test_load_remote_tool(gptscript):
    prg = await gptscript.load_file("github.com/gptscript-ai/context/workspace")
    assert prg.entryToolId != "", "Unexpected entry tool id from remote tool"
    assert len(prg.toolSet) > 0, "Unexpected number of tools in remote tool"
    assert prg.name != "", "Unexpected name from remote tool"


@pytest.mark.asyncio
async def test_load_simple_content(gptscript):
    wd = os.getcwd()
    with open(wd + "/tests/fixtures/test.gpt") as f:
        prg = await gptscript.load_content(f.read())
        assert prg.toolSet[prg.entryToolId].instructions == "Who was the president of the United States in 1986?", \
            "Unexpected output from parsing simple file"


@pytest.mark.asyncio
async def test_load_tools(gptscript, tool_list):
    prg = await gptscript.load_tools(tool_list)
    assert prg.entryToolId != "", "Unexpected entry tool id from remote tool"
    assert len(prg.toolSet) > 0, "Unexpected number of tools in remote tool"
    # Name will be empty in this case.
    assert prg.name == "", "Unexpected name from remote tool"


@pytest.mark.asyncio
async def test_parse_simple_file(gptscript):
    wd = os.getcwd()
    tools = await gptscript.parse(wd + "/tests/fixtures/test.gpt")
    assert len(tools) == 1, "Unexpected number of tools for parsing simple file"
    assert isinstance(tools[0], Tool), "Unexpected node type from parsing simple file"
    assert tools[0].instructions == "Who was the president of the United States in 1986?", \
        "Unexpected output from parsing simple file"


@pytest.mark.asyncio
async def test_parse_empty_file(gptscript):
    wd = os.getcwd()
    tools = await gptscript.parse(wd + "/tests//fixtures/empty.gpt")
    assert len(tools) == 0, "Unexpected number of tools for parsing emtpy file"


@pytest.mark.asyncio
async def test_parse_empty_str(gptscript):
    tools = await gptscript.parse_content("")
    assert len(tools) == 0, "Unexpected number of tools for parsing empty string"


@pytest.mark.asyncio
async def test_parse_tool_with_metadata(gptscript):
    wd = os.getcwd()
    tools = await gptscript.parse(wd + "/tests/fixtures/parse-with-metadata.gpt")
    assert len(tools) == 2, "Unexpected number of tools for parsing simple file"
    assert isinstance(tools[0], Tool), "Unexpected node type from parsing file with metadata"
    assert "requests.get(" in tools[0].instructions, "Unexpected output from parsing file with metadata"
    assert isinstance(tools[1], Text), "Unexpected node type from parsing file with metadata"
    assert tools[1].text == "requests", "Unexpected output from parsing file with metadata"
    assert tools[1].format == "metadata:foo:requirements.txt", "Unexpected output from parsing file with metadata"


@pytest.mark.asyncio
async def test_parse_tool(gptscript):
    tools = await gptscript.parse_content("echo hello")
    assert len(tools) == 1, "Unexpected number of tools for parsing tool"
    assert isinstance(tools[0], Tool), "Unexpected node type from parsing tool"
    assert tools[0].instructions == "echo hello", "Unexpected output from parsing tool"


@pytest.mark.asyncio
async def test_parse_tool_with_text_node(gptscript):
    tools = await gptscript.parse_content("echo hello\n---\n!markdown\nhello")
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
        "What is the second largest?",
        "What is the third one in the list?",
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
                for output in frame.output:
                    event_output += output.content

    cwd = os.getcwd().removesuffix("/tests")
    run = gptscript.run(cwd + "/tests/fixtures/global-tools.gpt",
                        Options(
                            disableCache=True,
                            credentialOverrides=["github.com/gptscript-ai/gateway:OPENAI_API_KEY"],
                        ),
                        event_handlers=[process_event],
                        )

    output = await run.text()
    assert "Hello!" in output, "Unexpected output from global tool test: " + output
    assert "Hello" in event_output, "Unexpected stream output from global tool test: " + event_output

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
        elif frame.type == RunEventType.callProgress or frame.type == RunEventType.callFinish:
            for output in frame.output:
                event_content += output.content

    tool = ToolDef(tools=["sys.exec"], instructions="List the files in the current directory as '.'.")
    out = await gptscript.evaluate(
        tool,
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
        elif frame.type == RunEventType.callProgress or frame.type == RunEventType.callFinish:
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
            assert "first name" in frame.fields[0].name, "Unexpected field: " + frame.fields[0].name
            await gptscript.prompt(PromptResponse(frame.id, {frame.fields[0].name: "Clicky"}))
        elif frame.type == RunEventType.callProgress or frame.type == RunEventType.callFinish:
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
async def test_prompt_with_metadata(gptscript):
    prompt_event_found = False

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal prompt_event_found
        if frame.type == RunEventType.prompt:
            prompt_event_found = True
            assert len(frame.fields) == 1, "Unexpected number of fields: " + str(frame.fields)
            assert "first name" in frame.fields[0].name, "Unexpected field: " + frame.fields[0].name
            assert "first_name" in frame.metadata, "Unexpected metadata: " + str(frame.metadata)
            assert frame.metadata["first_name"] == "Clicky", "Unexpected metadata: " + str(frame.metadata)
            await gptscript.prompt(PromptResponse(frame.id, {frame.fields[0].name: "Clicky"}))

    out = await gptscript.run(
        "sys.prompt",
        Options(prompt=True, disableCache=True, input='{"fields": "first name", "metadata": {"first_name": "Clicky"}}'),
        event_handlers=[process_event],
    ).text()

    assert prompt_event_found, "No prompt event"
    assert "Clicky" in out, "Unexpected output: " + out


@pytest.mark.asyncio
async def test_prompt_without_prompt_allowed(gptscript):
    prompt_event_found = False

    async def process_event(r: Run, frame: CallFrame | RunFrame | PromptFrame):
        nonlocal prompt_event_found
        if frame.type == RunEventType.prompt:
            prompt_event_found = True
            assert len(frame.fields) == 1, "Unexpected number of fields: " + str(frame.fields)
            assert "first name" in frame.fields[0].name, "Unexpected field: " + frame.fields[0].name
            await gptscript.prompt(PromptResponse(frame.id, {frame.fields[0].name: "Clicky"}))

    tool = ToolDef(
        tools=["sys.prompt"],
        instructions="Use the sys.prompt user to ask the user for 'first name' which is not sensitive. After you get their first name, say hello.",
    )
    run = gptscript.evaluate(
        tool,
        event_handlers=[process_event],
    )

    try:
        out = await run.text()
    except Exception as e:
        out = str(e)

    assert not prompt_event_found, "Prompt event occurred"
    assert "prompt event occurred" in out, "Unexpected output: " + out


def test_get_env():
    os.environ['TEST_ENV'] = json.dumps({
        '_gz': base64.b64encode(gzip.compress(b'test value')).decode('utf-8'),
    }).replace(' ', '')
    assert 'test value' == get_env('TEST_ENV')


@pytest.mark.asyncio
async def test_run_file_with_metadata(gptscript):
    run = gptscript.run("./tests/fixtures/parse-with-metadata.gpt")
    assert "200" == await run.text(), "Expect file to have correct output"


@pytest.mark.asyncio
async def test_parse_with_metadata_then_run(gptscript):
    cwd = os.getcwd().removesuffix("/tests")
    tools = await gptscript.parse(cwd + "/tests/fixtures/parse-with-metadata.gpt")
    run = gptscript.evaluate(tools[0])
    assert "200" == await run.text(), "Expect file to have correct output"


@pytest.mark.asyncio
async def test_credentials(gptscript):
    name = "test-" + str(os.urandom(4).hex())
    now = datetime.now()
    res = await gptscript.create_credential(
        Credential(toolName=name, env={"TEST": "test"}, expiresAt=now + timedelta(seconds=5),
                   checkParam="my-check-param"))
    assert not res.startswith("an error occurred"), "Unexpected error creating credential: " + res

    sleep(5)

    res = await gptscript.list_credentials()
    assert not str(res).startswith("an error occurred"), "Unexpected error listing credentials: " + str(res)
    assert len(res) > 0, "Expected at least one credential"
    for cred in res:
        if cred.toolName == name:
            assert cred.expiresAt < datetime.now(timezone.utc), "Expected credential to have expired"

    res = await gptscript.reveal_credential(name=name)
    assert not str(res).startswith("an error occurred"), "Unexpected error revealing credential: " + res
    assert res.env["TEST"] == "test", "Unexpected credential value: " + str(res)
    assert res.checkParam == "my-check-param", "Unexpected credential value: " + str(res)

    res = await gptscript.delete_credential(name=name)
    assert not res.startswith("an error occurred"), "Unexpected error deleting credential: " + res


@pytest.mark.asyncio
async def test_datasets(gptscript):
    os.environ["GPTSCRIPT_WORKSPACE_ID"] = await gptscript.create_workspace("directory")

    new_client = GPTScript(GlobalOptions(
        apiKey=os.getenv("OPENAI_API_KEY"),
        env=[f"{k}={v}" for k, v in os.environ.items()],
    ))

    # Create dataset
    dataset_id = await new_client.add_dataset_elements([
        DatasetElement(name="element1", contents="element1 contents", description="element1 description"),
        DatasetElement(name="element2", binaryContents=b"element2 contents", description="element2 description"),
    ], name="test-dataset", description="test dataset description")

    # Add two more elements
    await new_client.add_dataset_elements([
        DatasetElement(name="element3", contents="element3 contents", description="element3 description"),
        DatasetElement(name="element4", contents="element3 contents", description="element4 description"),
    ], datasetID=dataset_id)

    # Get the elements
    e1 = await new_client.get_dataset_element(dataset_id, "element1")
    assert e1.name == "element1", "Expected element name to match"
    assert e1.contents == "element1 contents", "Expected element contents to match"
    assert e1.description == "element1 description", "Expected element description to match"
    e2 = await new_client.get_dataset_element(dataset_id, "element2")
    assert e2.name == "element2", "Expected element name to match"
    assert e2.binaryContents == b"element2 contents", "Expected element contents to match"
    assert e2.description == "element2 description", "Expected element description to match"
    e3 = await new_client.get_dataset_element(dataset_id, "element3")
    assert e3.name == "element3", "Expected element name to match"
    assert e3.contents == "element3 contents", "Expected element contents to match"
    assert e3.description == "element3 description", "Expected element description to match"

    # List elements in the dataset
    elements = await new_client.list_dataset_elements(dataset_id)
    assert len(elements) == 4, "Expected four elements in the dataset"
    assert elements[0].name == "element1", "Expected element name to match"
    assert elements[0].description == "element1 description", "Expected element description to match"
    assert elements[1].name == "element2", "Expected element name to match"
    assert elements[1].description == "element2 description", "Expected element description to match"
    assert elements[2].name == "element3", "Expected element name to match"
    assert elements[2].description == "element3 description", "Expected element description to match"
    assert elements[3].name == "element4", "Expected element name to match"
    assert elements[3].description == "element4 description", "Expected element description to match"

    # List datasets
    datasets = await new_client.list_datasets()
    assert len(datasets) > 0, "Expected at least one dataset"
    assert datasets[0].id == dataset_id, "Expected dataset id to match"
    assert datasets[0].name == "test-dataset", "Expected dataset name to match"
    assert datasets[0].description == "test dataset description", "Expected dataset description to match"

    await gptscript.delete_workspace(os.environ["GPTSCRIPT_WORKSPACE_ID"])


@pytest.mark.asyncio
async def test_create_and_delete_workspace(gptscript):
    workspace_id = await gptscript.create_workspace("directory")
    assert workspace_id != "" and workspace_id.startswith("directory://"), "Expected workspace id to be set"
    await gptscript.delete_workspace(workspace_id)


@pytest.mark.asyncio
async def test_create_read_and_delete_file_in_workspace(gptscript):
    workspace_id = await gptscript.create_workspace("directory")
    await gptscript.write_file_in_workspace("test.txt", b"test", workspace_id)
    contents = await gptscript.read_file_in_workspace("test.txt", workspace_id)
    assert contents == b"test"

    file_info = await gptscript.stat_file_in_workspace("test.txt", workspace_id)
    assert file_info.name == "test.txt"
    assert file_info.size == 4
    assert file_info.modTime.hour == datetime.now(
        tz=file_info.modTime.tzinfo,
    ).hour and file_info.modTime < datetime.now(
        tz=file_info.modTime.tzinfo,
    )

    assert file_info.workspaceID == workspace_id
    await gptscript.delete_file_in_workspace("test.txt", workspace_id)
    await gptscript.delete_workspace(workspace_id)


@pytest.mark.asyncio
async def test_ls_complex_workspace(gptscript):
    workspace_id = await gptscript.create_workspace("directory")
    await gptscript.write_file_in_workspace("test/test1.txt", b"hello1", workspace_id)
    await gptscript.write_file_in_workspace("test1/test2.txt", b"hello2", workspace_id)
    await gptscript.write_file_in_workspace("test1/test3.txt", b"hello3", workspace_id)
    await gptscript.write_file_in_workspace(".hidden.txt", b"hidden", workspace_id)

    files = await gptscript.list_files_in_workspace(workspace_id)
    assert len(files) == 4

    files = await gptscript.list_files_in_workspace(workspace_id, prefix="test1")
    assert len(files) == 2

    await gptscript.remove_all(workspace_id, with_prefix="test1")

    files = await gptscript.list_files_in_workspace(workspace_id)
    assert len(files) == 2

    await gptscript.delete_workspace(workspace_id)


@pytest.mark.skipif(
    os.environ.get("AWS_ACCESS_KEY_ID") is None or os.environ.get("AWS_SECRET_ACCESS_KEY") is None,
    reason="AWS credentials not set",
)
@pytest.mark.asyncio
async def test_create_and_delete_workspace_s3(gptscript):
    workspace_id = await gptscript.create_workspace("s3")
    assert workspace_id != "" and workspace_id.startswith("s3://"), "Expected workspace id to be set"
    await gptscript.delete_workspace(workspace_id)


@pytest.mark.skipif(
    os.environ.get("AWS_ACCESS_KEY_ID") is None or os.environ.get("AWS_SECRET_ACCESS_KEY") is None,
    reason="AWS credentials not set",
)
@pytest.mark.asyncio
async def test_create_read_and_delete_file_in_workspaces3(gptscript):
    workspace_id = await gptscript.create_workspace("s3")
    await gptscript.write_file_in_workspace("test.txt", b"test", workspace_id)
    contents = await gptscript.read_file_in_workspace("test.txt", workspace_id)
    assert contents == b"test"

    file_info = await gptscript.stat_file_in_workspace("test.txt", workspace_id)
    assert file_info.name == "test.txt"
    assert file_info.size == 4
    assert file_info.modTime.hour == datetime.now(
        tz=file_info.modTime.tzinfo,
    ).hour and file_info.modTime < datetime.now(
        tz=file_info.modTime.tzinfo,
    )

    await gptscript.delete_file_in_workspace("test.txt", workspace_id)
    await gptscript.delete_workspace(workspace_id)


@pytest.mark.skipif(
    os.environ.get("AWS_ACCESS_KEY_ID") is None or os.environ.get("AWS_SECRET_ACCESS_KEY") is None,
    reason="AWS credentials not set",
)
@pytest.mark.asyncio
async def test_ls_complex_workspace_s3(gptscript):
    workspace_id = await gptscript.create_workspace("s3")
    await gptscript.write_file_in_workspace("test/test1.txt", b"hello1", workspace_id)
    await gptscript.write_file_in_workspace("test1/test2.txt", b"hello2", workspace_id)
    await gptscript.write_file_in_workspace("test1/test3.txt", b"hello3", workspace_id)
    await gptscript.write_file_in_workspace(".hidden.txt", b"hidden", workspace_id)

    files = await gptscript.list_files_in_workspace(workspace_id)
    assert len(files) == 4

    files = await gptscript.list_files_in_workspace(workspace_id, prefix="test1")
    assert len(files) == 2

    await gptscript.remove_all(workspace_id, with_prefix="test1")

    files = await gptscript.list_files_in_workspace(workspace_id)
    assert len(files) == 2

    await gptscript.delete_workspace(workspace_id)

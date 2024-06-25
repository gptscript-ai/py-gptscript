import asyncio

from gptscript.gptscript import GPTScript
from gptscript.text import Text
from gptscript.tool import Tool


async def main():
    g = GPTScript()
    nodes = [
        Text(fmt="nodeGraph", text='{"main":{"x":-692.5543409432609,"y":-114.63783459299711}}'),
        Tool(chat=True, tools=["sys.prompt"], context=["github.com/gptscript-ai/context/workspace"],
             instructions="Ask the user for their 'first name'. Then reply hello to the user."),
    ]
    print(await g.fmt(nodes))


asyncio.run(main())

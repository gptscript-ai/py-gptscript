class Tool:
    def __init__(
        self,
        name="",
        description="",
        tools=[],
        max_tokens=None,
        model="",
        cache=True,
        temperature=None,
        args={},
        internal_prompt="",
        instructions="",
        json_response=False,
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.max_tokens = max_tokens
        self.model = model
        self.cache = cache
        self.temperature = temperature
        self.args = args
        self.internal_prompt = internal_prompt
        self.instructions = instructions
        self.json_response = json_response

    def __str__(self):
        tool = ""
        if self.name != "":
            tool += f"Name: {self.name}\n"
        if self.description != "":
            tool += f"Description: {self.description}\n"
        if len(self.tools) > 0 and self.tools:
            tools = ", ".join(self.tools)
            tool += f"Tools: {tools}\n"
        if self.max_tokens is not None:
            tool += f"Max tokens: {self.max_tokens}\n"
        if self.model != "":
            tool += f"Model: {self.model}\n"
        if not self.cache:
            tool += "Cache: false\n"
        if self.temperature is not None:
            tool += f"Temperature: {self.temperature}\n"
        if self.json_response:
            tool += "JSON Response: true\n"
        if self.args:
            for arg, desc in self.args.items():
                tool += f"Args: {arg}: {desc}\n"
        if self.internal_prompt != "":
            tool += f"Internal prompt: {self.internal_prompt}\n"
        if self.instructions != "":
            tool += self.instructions

        return tool


class FreeForm:
    def __init__(self, content=""):
        self.content = content

    def __str__(self):
        return self.content

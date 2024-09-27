class PromptResponse:
    def __init__(self,
                 id: str = "",
                 responses: dict[str, str] = None,
                 **kwargs,
                 ):
        self.id = id
        self.responses = responses

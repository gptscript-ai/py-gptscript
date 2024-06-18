class PromptResponse:
    def __init__(self,
                 id: str = "",
                 responses: dict[str, str] = None,
                 ):
        self.id = id
        self.responses = responses

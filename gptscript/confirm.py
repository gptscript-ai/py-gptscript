class AuthResponse:
    def __init__(self,
                 id: str = "",
                 accept: bool = "",
                 message: str = "",
                 ):
        self.id = id
        self.accept = accept
        self.message = message

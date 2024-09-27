class AuthResponse:
    def __init__(self,
                 id: str = "",
                 accept: bool = "",
                 message: str = "",
                 **kwargs,
                 ):
        self.id = id
        self.accept = accept
        self.message = message

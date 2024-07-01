import os
from typing import Mapping


class GlobalOptions:
    def __init__(self, apiKey: str = "", baseURL: str = "", defaultModel: str = "", env: Mapping[str, str] = None):
        self.APIKey = apiKey
        self.BaseURL = baseURL
        self.DefaultModel = defaultModel
        self.Env = env

    def toEnv(self):
        if self.Env is None:
            self.Env = os.environ.copy()

        if self.APIKey != "":
            self.Env["OPENAI_API_KEY"] = self.APIKey
        if self.BaseURL != "":
            self.Env["OPENAI_BASE_URL"] = self.BaseURL
        if self.DefaultModel != "":
            self.Env["GPTSCRIPT_SDKSERVER_DEFAULT_MODEL"] = self.DefaultModel


class Options(GlobalOptions):
    def __init__(self,
                 input: str = "",
                 disableCache: bool = False,
                 subTool: str = "",
                 workspace: str = "",
                 chatState: str = "",
                 confirm: bool = False,
                 prompt: bool = False,
                 credentialOverrides: list[str] = None,
                 env: list[str] = None,
                 apiKey: str = "",
                 baseURL: str = "",
                 defaultModel: str = ""
                 ):
        super().__init__(apiKey, baseURL, defaultModel)
        self.input = input
        self.disableCache = disableCache
        self.subTool = subTool
        self.workspace = workspace
        self.chatState = chatState
        self.confirm = confirm
        self.prompt = prompt
        self.credentialOverrides = credentialOverrides
        self.env = env

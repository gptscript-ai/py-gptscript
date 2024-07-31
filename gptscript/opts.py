import os
from typing import Mapping


class GlobalOptions:
    def __init__(self,
                 apiKey: str = "", baseURL: str = "", defaultModelProvider: str = "", defaultModel: str = "",
                 env: Mapping[str, str] = None):
        self.APIKey = apiKey
        self.BaseURL = baseURL
        self.DefaultModel = defaultModel
        self.DefaultModelProvider = defaultModelProvider
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
        if self.DefaultModelProvider != "":
            self.Env["GPTSCRIPT_SDKSERVER_DEFAULT_MODEL_PROVIDER"] = self.DefaultModelProvider


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
                 location: str = "",
                 env: list[str] = None,
                 forceSequential: bool = False,
                 apiKey: str = "",
                 baseURL: str = "",
                 defaultModelProvider: str = "",
                 defaultModel: str = ""
                 ):
        super().__init__(apiKey, baseURL, defaultModelProvider, defaultModel)
        self.input = input
        self.disableCache = disableCache
        self.subTool = subTool
        self.workspace = workspace
        self.chatState = chatState
        self.confirm = confirm
        self.prompt = prompt
        self.credentialOverrides = credentialOverrides
        self.location = location
        self.env = env
        self.forceSequential = forceSequential

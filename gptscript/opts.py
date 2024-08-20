import os
from typing import Mapping, Self


class GlobalOptions:
    def __init__(
            self,
            apiKey: str = "",
            baseURL: str = "",
            defaultModelProvider: str = "",
            defaultModel: str = "",
            env: Mapping[str, str] = None,
    ):
        self.APIKey = apiKey
        self.BaseURL = baseURL
        self.DefaultModel = defaultModel
        self.DefaultModelProvider = defaultModelProvider
        if env is None:
            env = os.environ
        env_list = [f"{k}={v}" for k, v in env.items()]
        self.Env = env_list

    def merge(self, other: Self) -> Self:
        cp = self.__class__()
        if other is None:
            return cp
        cp.APIKey = other.APIKey if other.APIKey != "" else self.APIKey
        cp.BaseURL = other.BaseURL if other.BaseURL != "" else self.BaseURL
        cp.DefaultModel = other.DefaultModel if other.DefaultModel != "" else self.DefaultModel
        cp.DefaultModelProvider = other.DefaultModelProvider if other.DefaultModelProvider != "" else self.DefaultModelProvider
        cp.Env = (other.Env or []).extend(self.Env or [])
        return cp

    def toEnv(self):
        if self.Env is None:
            self.Env = [f"{k}={v}" for k, v in os.environ.items()]

        if self.APIKey != "":
            self.Env.append(f"OPENAI_API_KEY={self.APIKey}")
        if self.BaseURL != "":
            self.Env.append(f"OPENAI_BASE_URL={self.BaseURL}")
        if self.DefaultModel != "":
            self.Env.append(f"GPTSCRIPT_SDKSERVER_DEFAULT_MODEL={self.DefaultModel}")
        if self.DefaultModelProvider != "":
            self.Env.append(f"GPTSCRIPT_SDKSERVER_DEFAULT_MODEL_PROVIDER={self.DefaultModelProvider}")


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

    def merge_global_opts(self, other: GlobalOptions) -> Self:
        cp = super().merge(other)
        if other is None:
            return cp
        cp.input = self.input
        cp.disableCache = self.disableCache
        cp.subTool = self.subTool
        cp.workspace = self.workspace
        cp.chatState = self.chatState
        cp.confirm = self.confirm
        cp.prompt = self.prompt
        cp.credentialOverrides = self.credentialOverrides
        cp.location = self.location
        cp.env = self.env
        cp.forceSequential = self.forceSequential
        return cp

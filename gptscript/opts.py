import os
from typing import Self


class GlobalOptions:
    def __init__(
            self,
            url: str = "",
            token: str = "",
            apiKey: str = "",
            baseURL: str = "",
            defaultModelProvider: str = "",
            defaultModel: str = "",
            cacheDir: str = "",
            datasetTool: str = "",
            workspaceTool: str = "",
            env: list[str] = None,
    ):
        self.URL = url
        self.Token = token
        self.APIKey = apiKey
        self.BaseURL = baseURL
        self.DefaultModel = defaultModel
        self.DefaultModelProvider = defaultModelProvider
        self.CacheDir = cacheDir
        self.DatasetTool = datasetTool
        self.WorkspaceTool = workspaceTool
        if env is None:
            env = [f"{k}={v}" for k, v in os.environ.items()]
        elif isinstance(env, dict):
            env = [f"{k}={v}" for k, v in env.items()]
        self.Env = env

    def merge(self, other: Self) -> Self:
        cp = self.__class__()
        if other is None:
            return self
        cp.URL = other.URL if other.URL != "" else self.URL
        cp.Token = other.Token if other.Token != "" else self.Token
        cp.APIKey = other.APIKey if other.APIKey != "" else self.APIKey
        cp.BaseURL = other.BaseURL if other.BaseURL != "" else self.BaseURL
        cp.DefaultModel = other.DefaultModel if other.DefaultModel != "" else self.DefaultModel
        cp.DefaultModelProvider = other.DefaultModelProvider if other.DefaultModelProvider != "" else self.DefaultModelProvider
        cp.CacheDir = other.CacheDir if other.CacheDir != "" else self.CacheDir
        cp.DatasetTool = other.DatasetTool if other.DatasetTool != "" else self.DatasetTool
        cp.WorkspaceTool = other.WorkspaceTool if other.WorkspaceTool != "" else self.WorkspaceTool
        cp.Env = (other.Env or [])
        cp.Env.extend(self.Env or [])
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
                 credentialContexts: list[str] = None,
                 location: str = "",
                 env: list[str] = None,
                 forceSequential: bool = False,
                 url: str = "",
                 token: str = "",
                 apiKey: str = "",
                 baseURL: str = "",
                 defaultModelProvider: str = "",
                 defaultModel: str = "",
                 cacheDir: str = "",
                 datasetToolDir: str = "",
                 workspaceTool: str = "",
                 ):
        super().__init__(url, token, apiKey, baseURL, defaultModelProvider, defaultModel, cacheDir, datasetToolDir,
                         workspaceTool, env)
        self.input = input
        self.disableCache = disableCache
        self.subTool = subTool
        self.workspace = workspace
        self.chatState = chatState
        self.confirm = confirm
        self.prompt = prompt
        self.credentialOverrides = credentialOverrides
        self.credentialContexts = credentialContexts
        self.location = location
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
        cp.credentialContexts = self.credentialContexts
        cp.location = self.location
        cp.forceSequential = self.forceSequential
        return cp

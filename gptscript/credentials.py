import json
from datetime import datetime, timezone
from enum import Enum
from typing import List


def is_timezone_aware(dt: datetime):
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


class CredentialType(Enum):
    Tool = "tool",
    ModelProvider = "modelProvider"


class Credential:
    def __init__(self,
                 context: str = "default",
                 toolName: str = "",
                 type: CredentialType = CredentialType.Tool,
                 env: dict[str, str] = None,
                 ephemeral: bool = False,
                 expiresAt: datetime = None,
                 refreshToken: str = "",
                 ):
        self.context = context
        self.toolName = toolName
        self.type = type
        self.env = env
        self.ephemeral = ephemeral
        self.expiresAt = expiresAt
        self.refreshToken = refreshToken

        if self.env is None:
            self.env = {}

    def to_json(self):
        datetime_str = ""

        if self.expiresAt is not None:
            system_tz = datetime.now().astimezone().tzinfo

            if not is_timezone_aware(self.expiresAt):
                self.expiresAt = self.expiresAt.replace(tzinfo=system_tz)
                datetime_str = self.expiresAt.isoformat()

                # For UTC only, replace the "+00:00" with "Z"
                if self.expiresAt.tzinfo == timezone.utc:
                    datetime_str = datetime_str.replace("+00:00", "Z")

        req = {
            "context": self.context,
            "toolName": self.toolName,
            "type": self.type.value[0],
            "env": self.env,
            "ephemeral": self.ephemeral,
            "refreshToken": self.refreshToken,
        }

        if datetime_str != "":
            req["expiresAt"] = datetime_str

        return json.dumps(req)

class CredentialRequest:
    def __init__(self,
                 content: str = "",
                 allContexts: bool = False,
                 contexts: List[str] = None,
                 name: str = "",
                 ):
        if contexts is None:
            contexts = ["default"]

        self.content = content
        self.allContexts = allContexts
        self.contexts = contexts
        self.name = name

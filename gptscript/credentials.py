import json
from datetime import datetime, timezone
from enum import Enum
from typing import List


def is_timezone_aware(dt: datetime):
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


class CredentialType(Enum):
    tool = "tool",
    modelProvider = "modelProvider"


class Credential:
    def __init__(self,
                 context: str = "default",
                 toolName: str = "",
                 type: CredentialType = CredentialType.tool,
                 env: dict[str, str] = None,
                 ephemeral: bool = False,
                 expiresAt: datetime = None,
                 refreshToken: str = "",
                 checkParam: str = "",
                 **kwargs,
                 ):
        self.context = context
        self.toolName = toolName
        self.type = type
        self.env = env
        self.ephemeral = ephemeral
        self.expiresAt = expiresAt
        self.refreshToken = refreshToken
        self.checkParam = checkParam

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
            "checkParam": self.checkParam,
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


def to_credential(c) -> Credential:
    expiresAt = c["expiresAt"]
    if expiresAt is not None:
        if expiresAt.endswith("Z"):
            expiresAt = expiresAt.replace("Z", "+00:00")
        expiresAt = datetime.fromisoformat(expiresAt)

    return Credential(
        context=c["context"],
        toolName=c["toolName"],
        type=CredentialType[c["type"]],
        env=c["env"],
        ephemeral=c.get("ephemeral", False),
        expiresAt=expiresAt,
        refreshToken=c["refreshToken"],
        checkParam=c.get("checkParam", "")
    )

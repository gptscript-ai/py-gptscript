import base64
from pydantic import BaseModel, field_serializer, field_validator, BeforeValidator


class DatasetMeta(BaseModel):
    id: str
    name: str
    description: str


class DatasetElementMeta(BaseModel):
    name: str
    description: str


class DatasetElement(BaseModel):
    name: str
    description: str = ""
    contents: str = ""
    binaryContents: bytes = b""

    @field_serializer("binaryContents")
    def serialize_contents(self, value: bytes) -> str:
        return base64.b64encode(value).decode("utf-8")

    @field_validator("binaryContents", mode="before")
    def deserialize_contents(cls, value) -> bytes:
        if isinstance(value, str):
            return base64.b64decode(value)
        return value


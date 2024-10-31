import base64
from typing import Dict
from pydantic import BaseModel, field_serializer, field_validator, BeforeValidator


class DatasetElementMeta(BaseModel):
    name: str
    description: str


class DatasetElement(BaseModel):
    name: str
    description: str
    contents: bytes

    @field_serializer("contents")
    def serialize_contents(self, value: bytes) -> str:
        return base64.b64encode(value).decode("utf-8")

    @field_validator("contents", mode="before")
    def deserialize_contents(cls, value) -> bytes:
        if isinstance(value, str):
            return base64.b64decode(value)
        return value


class DatasetMeta(BaseModel):
    id: str
    name: str
    description: str


class Dataset(BaseModel):
    id: str
    name: str
    description: str
    elements: Dict[str, DatasetElementMeta]

from typing import Dict
from pydantic import BaseModel

class DatasetElementMeta(BaseModel):
    name: str
    description: str


class DatasetElement(BaseModel):
    name: str
    description: str
    contents: str


class DatasetMeta(BaseModel):
    id: str
    name: str
    description: str


class Dataset(BaseModel):
    id: str
    name: str
    description: str
    elements: Dict[str, DatasetElementMeta]

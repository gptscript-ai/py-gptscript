from pydantic import BaseModel, conlist
from typing import Any, Dict, Optional


class Permission(BaseModel):
    created: int
    id: str
    object: str
    allow_create_engine: bool
    allow_sampling: bool
    allow_logprobs: bool
    allow_search_indices: bool
    allow_view: bool
    allow_fine_tuning: bool
    organization: str
    group: Any
    is_blocking: bool


class Model(BaseModel):
    created: Optional[int]
    id: str
    object: str
    owned_by: str
    permission: Optional[conlist(Permission)]
    root: Optional[str]
    parent: Optional[str]
    metadata: Optional[Dict[str, str]]

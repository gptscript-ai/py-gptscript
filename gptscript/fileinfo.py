from datetime import datetime

from pydantic import BaseModel


class FileInfo(BaseModel):
    workspaceID: str
    name: str
    size: int
    modTime: datetime

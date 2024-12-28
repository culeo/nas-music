from pydantic import BaseModel
from typing import Optional

class PlaylistBase(BaseModel):
    raw_id: str
    track_update_time: int
    coverImgUrl: str = ""
    name: str = ""
    platform: str = "ncm"

class PlaylistSave(PlaylistBase):
    id: Optional[int] = 0  # 保存时可选，默认为 0

class PlaylistInDB(PlaylistBase):
    id: int

    class Config:
        from_attributes = True
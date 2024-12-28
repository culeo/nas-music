from pydantic import BaseModel
from typing import Optional

class SongBase(BaseModel):
    raw_id: str
    playlist_id: int
    state: int = 0
    name: str = ""
    artist: str = ""
    album: str = ""
    album_cover: str = ""

class SongSave(SongBase):
    id: Optional[int] = 0  # 保存时可选，默认为 0

class SongInDB(SongBase):
    id: int  # 输出时需要 id 字段

    class Config:
        from_attributes = True  # 启用 ORM 模式以支持 SQLAlchemy 对象
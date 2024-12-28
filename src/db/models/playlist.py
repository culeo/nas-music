from src.db.base_class import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.db.models.song import Song

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    raw_id = Column(String, nullable=False)
    track_update_time = Column(Integer)
    platform = Column(String, default="ncm")
    state = Column(Integer, default=0)  # 0: 未同步完成, 1: 已同步完成
    coverImgUrl = Column(String, default="")  # 新增字段，默认值为空字符串
    name = Column(String, default="")  # 新增字段，默认值为空字符串

Playlist.songs = relationship("Song", order_by=Song.id, back_populates="playlist")

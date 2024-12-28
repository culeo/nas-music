from src.db.base_class import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    raw_id = Column(String)
    state = Column(Integer, default=0)  # 0: 未下载, 1: 已下载
    name = Column(String, default="")  # 新增字段
    artist = Column(String, default="")  # 新增字段
    album = Column(String, default="")  # 新增字段
    album_cover = Column(String, default="")  # 新增字段
    playlist = relationship("Playlist", back_populates="songs")


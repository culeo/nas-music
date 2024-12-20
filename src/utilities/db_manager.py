from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from contextlib import contextmanager
from src.utilities.paths import get_database_file_path  # 导入路径管理函数

Base = declarative_base()


class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_id = Column(String, nullable=False)
    track_update_time = Column(Integer)
    platform = Column(String, default="ncm")
    state = Column(Integer, default=0)  # 0: 未同步完成, 1: 已同步完成
    coverImgUrl = Column(String, default="")  # 新增字段，默认值为空字符串
    name = Column(String, default="")  # 新增字段，默认值为空字符串


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


Playlist.songs = relationship("Song", order_by=Song.id, back_populates="playlist")


class DBManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "engine"):
            db_path = f"sqlite:///{get_database_file_path()}"
            self.engine = create_engine(db_path)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_track_update_time(self, session, raw_id):
        playlist = session.query(Playlist).filter_by(raw_id=raw_id).first()
        return playlist.track_update_time if playlist else None

    def save_playlist(
        self, session, raw_id, track_update_time, coverImgUrl="", name=""
    ):
        playlist = session.query(Playlist).filter_by(raw_id=raw_id).first()
        if not playlist:
            playlist = Playlist(
                raw_id=raw_id,
                track_update_time=track_update_time,
                coverImgUrl=coverImgUrl,
                name=name,
            )
            session.add(playlist)
        else:
            if playlist.track_update_time != track_update_time:
                playlist.track_update_time = track_update_time
                playlist.state = 0  # 重置状态
            # 更新封面和名称
            playlist.coverImgUrl = coverImgUrl
            playlist.name = name

    def save_song(
        self, session, playlist_id, song_raw_id, name, artist, album, album_cover
    ):
        song = (
            session.query(Song)
            .filter_by(playlist_id=playlist_id, raw_id=song_raw_id)
            .first()
        )
        if not song:
            song = Song(
                playlist_id=playlist_id,
                raw_id=song_raw_id,
                name=name,
                artist=artist,
                album=album,
                album_cover=album_cover,
            )
            session.add(song)

    def update_song_state(self, session, song_id, state):
        song = session.query(Song).filter_by(id=song_id).first()
        if song:
            song.state = state

    def update_playlist_state(self, session, raw_id, state):
        playlist = session.query(Playlist).filter_by(raw_id=raw_id).first()
        if playlist:
            playlist.state = state

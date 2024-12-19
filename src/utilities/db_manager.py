from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from src.utilities.paths import get_database_file_path  # 导入路径管理函数

Base = declarative_base()

class Playlist(Base):
    __tablename__ = 'playlists'
    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, unique=True, nullable=False)
    track_update_time = Column(Integer)
    platform = Column(String, default='ncm')

class Download(Base):
    __tablename__ = 'downloads'
    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('playlists.playlist_id'))
    song_id = Column(Integer)
    playlist = relationship("Playlist", back_populates="downloads")

Playlist.downloads = relationship("Download", order_by=Download.id, back_populates="playlist")

class DBManager:
    def __init__(self):
        db_path = f'sqlite:///{get_database_file_path()}'
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def get_track_update_time(self, session, playlist_id):
        playlist = session.query(Playlist).filter_by(playlist_id=playlist_id).first()
        return playlist.track_update_time if playlist else None

    def is_song_downloaded(self, session, playlist_id, song_id):
        return session.query(Download).filter_by(playlist_id=playlist_id, song_id=song_id).first() is not None

    def save_song_download_info(self, session, playlist_id, song_id):
        if not self.is_song_downloaded(session, playlist_id, song_id):
            download = Download(playlist_id=playlist_id, song_id=song_id)
            session.add(download)
        session.commit()

    def update_playlist_track_update_time(self, session, playlist_id, track_update_time):
        playlist = session.query(Playlist).filter_by(playlist_id=playlist_id).first()
        if not playlist:
            playlist = Playlist(playlist_id=playlist_id, track_update_time=track_update_time)
            session.add(playlist)
        else:
            playlist.track_update_time = track_update_time
        session.commit()
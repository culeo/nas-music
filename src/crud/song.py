from sqlalchemy.orm import Session
from src.db.models.playlist import Playlist
from src.db.models.song import Song
from src.schemas.song import SongInDB, SongSave
from typing import List

class SongCRUD:
    def save_song(self, db: Session, song_data: SongSave) -> SongInDB:
        if song_data.id is None:
            song = db.query(Song).filter(Song.raw_id == song_data.raw_id, Song.playlist_id == song_data.playlist_id).first()
        else:
            song = db.query(Song).filter(Song.id == song_data.id).first()
        if song is None:
            # 创建新记录
            new_song = Song(**song_data.model_dump(exclude={"id"}))  # 排除 id
            db.add(new_song)
            db.commit()
            db.refresh(new_song)
            return SongInDB.model_validate(new_song)
        else:
            # 更新现有记录
            db_song = db.query(Song).filter(Song.id == song_data.id).first()
            if not db_song:
                raise ValueError("Song with the given ID does not exist")
            
            # 更新字段
            for field, value in song_data.model_dump(exclude={"id"}).items():
                setattr(db_song, field, value)
            db.commit()
            db.refresh(db_song)
            return SongInDB.model_validate(db_song)

    def get_song(self, db: Session, song_id: int) -> SongInDB | None:
        """
        根据 ID 获取一首歌曲
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        return SongInDB.model_validate(song) if song else None

    def get_all_songs(self, db: Session, playlist_id: int, skip: int = 0, limit: int = 10) -> List[SongInDB]:
        """
        获取指定播放列表中的歌曲，支持分页
        """
        songs = db.query(Song).filter(Song.playlist_id == playlist_id).offset(skip).limit(limit).all()
        return [SongInDB.model_validate(song) for song in songs]

    def get_total_songs(self, db: Session, playlist_id: int) -> int:
        """
        获取指定播放列表中的歌曲总数
        """
        return db.query(Song).filter(Song.playlist_id == playlist_id).count()

    def get_all_wait_download_songs(self, db: Session, user_id: int) -> List[SongInDB]:
        """
        获取待下载的歌曲列表
        """
        songs = db.query(Song).join(Playlist).filter(Playlist.user_id == user_id, Song.state == 0).all()
        return [SongInDB.model_validate(song) for song in songs]

    def update_song_state(self, db: Session, id: int, state: int) -> SongInDB:
        """
        更新歌曲状态
        """
        song = db.query(Song).filter(Song.id == id).first()
        song.state = state
        db.commit()
        return SongInDB.model_validate(song)
   
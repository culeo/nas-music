from sqlalchemy.orm import Session
from src.db.models.playlist import Playlist
from src.schemas.playlist import PlaylistSave, PlaylistInDB
from typing import List

class PlaylistCRUD:
    def save_playlist(self, db: Session, user_id: int, playlist_data: PlaylistSave) -> PlaylistInDB:
        if playlist_data.id is None:
            playlist = db.query(Playlist).filter_by(user_id=user_id, raw_id=playlist_data.raw_id, platform=playlist_data.platform).first()
        else:
            playlist = db.query(Playlist).filter_by(id=playlist_data.id).first()
        if not playlist:
            playlist = Playlist(**playlist_data.model_dump(exclude={"id"}))
            playlist.user_id = user_id
            db.add(playlist)
            db.commit()
            db.refresh(playlist)
            return PlaylistInDB.model_validate(playlist)
        else:
            for key, value in playlist_data.model_dump(exclude_unset=True).items():
                setattr(playlist, key, value)
            db.commit()
            db.refresh(playlist)
            return PlaylistInDB.model_validate(playlist)

    def get_playlist(self, db: Session, user_id: int, raw_id: str, platform: str) -> PlaylistInDB:
        playlist = db.query(Playlist).filter_by(user_id=user_id, raw_id=raw_id, platform=platform).first()
        return PlaylistInDB.model_validate(playlist) if playlist else None

    def get_all_playlists(self, db: Session, user_id: int, page: int = 1, page_size: int = 10) -> List[PlaylistInDB]:
        offset = (page - 1) * page_size
        playlists = db.query(Playlist).filter_by(user_id=user_id).offset(offset).limit(page_size).all()
        return [PlaylistInDB.model_validate(playlist) for playlist in playlists]

    def get_total_playlists(self, db: Session, user_id: int) -> int:
        return db.query(Playlist).filter_by(user_id=user_id).count()

    def verify_playlist_exists(self, db: Session, id: int, user_id: int) -> bool:
        return db.query(Playlist).filter_by(id=id, user_id=user_id).first() is not None

    def check_playlist_state(self, db: Session, user_id: int):
        playlists = db.query(Playlist).filter_by(user_id=user_id, state=0).all()
        for playlist in playlists:
            if all(song.state != 0 for song in playlist.songs):
                playlist.state = 1
            else:
                playlist.state = 0
        db.commit()
        
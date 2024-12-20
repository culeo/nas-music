from fastapi import APIRouter, HTTPException, Query
from src.utilities.db_manager import DBManager, Playlist, Song

router = APIRouter()
db_manager = DBManager()


@router.get("/playlists/")
async def get_playlists(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)):
    with db_manager.session_scope() as session:
        playlists_query = (
            session.query(Playlist)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "playlists": [
                {
                    "id": playlist.id,
                    "raw_id": playlist.raw_id,
                    "track_update_time": playlist.track_update_time,
                    "platform": playlist.platform,
                    "state": playlist.state,
                    "coverImgUrl": playlist.coverImgUrl,
                    "name": playlist.name,
                }
                for playlist in playlists_query
            ]
        }


@router.get("/playlists/{playlist_id}/songs/")
async def get_songs(playlist_id: int):
    with db_manager.session_scope() as session:
        playlist = session.query(Playlist).filter_by(id=playlist_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        songs_query = session.query(Song).filter_by(playlist_id=playlist_id).all()
        return {
            "songs": [
                {
                    "id": song.id,
                    "raw_id": song.raw_id,
                    "name": song.name,
                    "artist": song.artist,
                    "album": song.album,
                    "album_cover": song.album_cover,
                    "state": song.state,
                }
                for song in songs_query
            ]
        }

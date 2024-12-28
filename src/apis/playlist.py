from fastapi import APIRouter, HTTPException, Query, Depends
from src.utilities.auth import get_current_user
from loguru import logger
import asyncio
from src.db.session import SessionLocal
from src.crud.playlist import PlaylistCRUD
from src.crud.song import SongCRUD
from src.crud.user_preference import UserPreferenceCRUD
from src.scheduler import scheduler
from src.schemas.user_preference import NCM_SESSION

router = APIRouter()
playlist_crud = PlaylistCRUD()
song_crud = SongCRUD()
user_preference_crud = UserPreferenceCRUD()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/playlists")
async def get_playlists(
    page: int = Query(1, ge=1), 
    page_size: int = Query(10, ge=1), 
    uid: str = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    playlists = playlist_crud.get_all_playlists(db, uid, page, page_size)
    total = playlist_crud.get_total_playlists(db, uid)
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "total": total,
            "items": playlists
        }
    }

@router.get("/playlists/sync")
async def sync_playlists(uid: str = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    asyncio.create_task(scheduler.trigger_sync_playlists_task())
    if user_preference_crud.get_user_preference(db=db, user_id=uid, key=NCM_SESSION) is None:
        return {
            "code": 9999,
            "message": "没有登录可同步的账号",
        }
    return {
        "code": 0,
        "message": "已触发同步任务",
    }

@router.get("/playlists/{playlist_id}/songs")
async def get_songs(
    playlist_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    uid: str = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    if not playlist_crud.verify_playlist_exists(db, playlist_id, uid):
        raise HTTPException(status_code=404, detail={"code": 10001, "message": "歌单不存在"})

    offset = (page - 1) * page_size
    songs = song_crud.get_all_songs(db, playlist_id, offset, page_size)
    total = song_crud.get_total_songs(db, playlist_id)
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "total": total,
            "items": songs
        }
    }

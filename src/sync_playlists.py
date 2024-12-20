import os
import pyncm
from loguru import logger
from pyncm.apis.user import GetUserPlaylists
from pyncm.apis.playlist import GetPlaylistAllTracks
import asyncio
from src.utilities.tools import random_delay
from src.utilities.db_manager import (
    DBManager,
    Playlist,
)  # 导入 DBManager 和 Playlist 类

# 初始化数据库管理器
db_manager = DBManager()


async def sync_ncm_playlists():
    # 在这里执行定时查询状态的逻辑
    status = pyncm.apis.login.GetCurrentLoginStatus()
    playlists = GetUserPlaylists(status["account"]["id"])
    logger.debug(f"歌单: {playlists}")

    for playlist in playlists["playlist"]:
        logger.info(f"开始同步歌单: {playlist['name']}")

        # 创建临时变量 raw_playlist_id
        raw_playlist_id = playlist["id"]

        with db_manager.session_scope() as session:
            # 检查数据库中的 trackUpdateTime
            track_update_time = db_manager.get_track_update_time(
                session, raw_playlist_id
            )
            if track_update_time == playlist["trackUpdateTime"]:
                logger.info(f"歌单 {playlist['name']} 未更新，跳过")
                continue

            # 保存或更新歌单信息
            db_manager.save_playlist(
                session,
                raw_playlist_id,
                playlist["trackUpdateTime"],
                playlist["coverImgUrl"],
                playlist["name"],
            )

            # 获取歌单 ID
            playlist_id = (
                session.query(Playlist).filter_by(raw_id=raw_playlist_id).first().id
            )

        await random_delay()

        # 获取歌曲列表
        tracks = GetPlaylistAllTracks(raw_playlist_id)
        logger.debug(f"歌曲列表: {tracks}")

        for song in tracks["songs"]:
            # 提取歌曲信息
            song_name = song["name"]
            artist_name = ", ".join([artist["name"] for artist in song["ar"]])
            album_name = song["al"]["name"]
            album_cover = song["al"]["picUrl"]

            with db_manager.session_scope() as session:
                # 保存歌曲信息
                db_manager.save_song(
                    session,
                    playlist_id,
                    song["id"],
                    song_name,
                    artist_name,
                    album_name,
                    album_cover,
                )
    logger.info(f"NCM 歌单同步完成")


async def sync_playlists():
    # 调用 sync_ncm_playlists
    await sync_ncm_playlists()

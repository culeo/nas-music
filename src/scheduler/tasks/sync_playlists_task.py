import os, asyncio, httpx
import pyncm, random
from loguru import logger
from pyncm.apis.user import GetUserPlaylists
from pyncm.apis.login import GetCurrentLoginStatus
from pyncm.apis.playlist import GetPlaylistAllTracks
from src.db.session import SessionLocal
from src.schemas.playlist import PlaylistSave
from src.schemas.song import SongSave, SongInDB
from src.utilities.tools import random_delay
from src.crud.playlist import PlaylistCRUD
from src.crud.song import SongCRUD
from src.crud.user import UserCRUD
from src.crud.user_preference import UserPreferenceCRUD
from src.schemas.user_preference import NCM_SESSION
from src.utilities.third_plugins import ThirdPlugins
from src.utilities.paths import get_download_dir_path
from src.utilities.metadata_writer import write_metadata
from difflib import SequenceMatcher

third_plugins = ThirdPlugins()
user_crud = UserCRUD()
user_preference_crud = UserPreferenceCRUD()
playlist_crud = PlaylistCRUD()
song_crud = SongCRUD()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def sync_ncm_playlists(user_id: str):
    with next(get_db()) as db:
        session_str = user_preference_crud.get_user_preference(db=db, user_id=user_id, key=NCM_SESSION)
    if not session_str:
        logger.info(f"用户 {user_id} 未登录,跳过")
        return
    session = pyncm.LoadSessionFromString(session_str)
    pyncm.SetCurrentSession(session)
    # 在这里执行定时查询状态的逻辑
    status = GetCurrentLoginStatus()
    logger.debug(f"登录状态: {status}")

    playlists = GetUserPlaylists(status["account"]["id"])
    logger.debug(f"歌单: {playlists}")

    for playlist in playlists["playlist"]:
        logger.info(f"开始同步歌单: {playlist['name']}")
        # 创建临时变量 raw_playlist_id
        raw_playlist_id = str(playlist["id"])
        with next(get_db()) as db:
            db_playlist = playlist_crud.get_playlist(db=db, user_id=user_id, raw_id=raw_playlist_id, platform="ncm")
        if db_playlist and db_playlist.track_update_time == playlist["trackUpdateTime"]:
            logger.info(f"歌单 {playlist['name']} 未更新，跳过")
            continue
        update_playlist = PlaylistSave(
            raw_id=raw_playlist_id,
            name=playlist["name"],
            platform="ncm",
            track_update_time=playlist["trackUpdateTime"],
            coverImgUrl=playlist["coverImgUrl"],
            state=0
        )
        with next(get_db()) as db:
            db_playlist = playlist_crud.save_playlist(db=db, user_id=user_id, playlist_data=update_playlist) 
        await random_delay()

        # 获取歌曲列表
        tracks = GetPlaylistAllTracks(raw_playlist_id)
        logger.debug(f"歌曲列表: {tracks}")

        for song in tracks["songs"]:
            db_song = SongSave(
                raw_id=str(song["id"]),
                playlist_id=db_playlist.id,
                name=song.get("name", ""),
                platform="ncm",
                album=song["al"]["name"],
                artist=", ".join([artist.get("name", "") for artist in song.get("ar", [])]),
                album_cover=song.get("al", {}).get("picUrl", ""),
            )
            with next(get_db()) as db:
                song_crud.save_song(db=db, song_data=db_song)
            
    logger.info(f"NCM 歌单同步完成")

def sort_by_similar(plugin: str, song: SongInDB, result: list):
    matches = []
    logger.debug(f"歌曲: {song.name} - {song.artist}")
    for item in result.get("data", []):
        item_title = item.get("title", "")
        item_artist = item.get("artist", "")

        title_similarity = SequenceMatcher(None, song.name, item_title).ratio()
        artist_similarity = SequenceMatcher(None, song.artist, item_artist).ratio()
        weighted_similarity = 0.4 * title_similarity + 0.6 * artist_similarity

        matches.append((plugin, item, weighted_similarity))
      
    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches

async def download_song_from_plugin(result: list) -> str | None:
    for plugin, item, similarity in result:
        logger.info(f"插件 {plugin} 匹配度 {similarity:.2f}: {item}")

        # 获取媒体资源连接
        media_source = await third_plugins.get_media_source(
            item, "super", plugin=plugin
        )
        logger.debug(f"媒体资源: {media_source}")
        
        media_url = media_source.get("url", "")
        if len(media_url) > 0:
            # 下载文件
            file_path = os.path.join(
                get_download_dir_path(),
                f"{item['title']}-{item['artist']}.mp3",
            )
            is_success = await download_file(media_url, file_path)
            if is_success:
                # 调用封装的元数据写入方法
                write_metadata(file_path, item)

                # 获取歌词
                lyric_path = os.path.join(
                    get_download_dir_path(),
                    f"{item['title']}-{item['artist']}.lrc",
                )
                lyric_data = (
                    (await third_plugins.get_lyric(item, plugin=plugin))
                    .get("rawLrc", "")
                )
                with open(lyric_path, "w", encoding="utf-8") as f:
                    f.write(lyric_data)

                return file_path
            else:
                logger.warning(f"下载失败: {item}")

    return None  # 如果所有尝试都失败，返回 None

async def download_file(url, file_path):
    try:
        # 检查文件是否已经存在
        if os.path.exists(file_path):
            logger.info(f"文件已存在，跳过下载: {file_path}")
            return True

        async with httpx.AsyncClient() as client:
            # 发起请求
            async with client.stream("GET", url) as response:
                response.raise_for_status()  # 检查是否有HTTP错误
                
                # 打开文件写入
                with open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        logger.info(f"下载完成: {file_path}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return False

async def batch_download_ncm_playlists(user_id: int):
    logger.info("开始下载 NCM 歌单")

    with next(get_db()) as db:
        wait_download_songs = song_crud.get_all_wait_download_songs(db = db, user_id=user_id)
        logger.info(f"待下载歌曲数量: {len(wait_download_songs)}")

    for song in wait_download_songs:
        logger.debug(f"正在处理歌曲: {song.name}")
        all_results = []
        async for plugin, result in third_plugins.search(query=song.name, page=1, type="music"):
            if len(result) == 0:
                logger.warning(f"{plugin} 未找到匹配的歌曲: {song.name}")
                continue
            
            result = sort_by_similar(plugin=plugin, song=song, result=result)
            all_results.append(result)
            if result[0][2] > 0.95:
                break
            await random_delay()

        all_results.sort(key=lambda x: x[2], reverse=True)
    
        for result in all_results:
            await random_delay()
            file_path = await download_song_from_plugin(result)
            if file_path:
                song_crud.update_song_state(db=db, id=song.id, state=1)
                sleep_time = 5 * 60 + random.randint(1, 10)
                logger.info(f"歌曲下载完成: {song.name}, 等待 {sleep_time} 秒，进行下一次")
                await asyncio.sleep(sleep_time)
                break
            await random_delay()

    playlist_crud.check_playlist_state(db=db, user_id=user_id)

async def sync_playlists_task():
    with next(get_db()) as db:
        user_ids = user_crud.get_all_user_ids(db=db)
    for user_id in user_ids:
        await sync_ncm_playlists(user_id=user_id)
        await batch_download_ncm_playlists(user_id=user_id)

import os
import pyncm
from loguru import logger
from pyncm.apis.user import GetUserPlaylists
from pyncm.apis.playlist import GetPlaylistAllTracks
import asyncio
import requests
from src.music_source import MusicSource  # 导入 MusicSource 类
from src.utilities.tools import random_delay  # 导入 random_delay 方法
from src.utilities.db_manager import DBManager  # 导入 DBManager 类
from difflib import SequenceMatcher  # 用于计算字符串相似度
from src.utilities.paths import get_download_dir_path
from src.utilities.metadata_writer import write_metadata

# 初始化数据库管理器
db_manager = DBManager()

music_source = MusicSource()

def find_most_similar(song, results):
    matches = []

    song_name = song.get('name', '')
    artist_name = song.get('ar', [{}])[0].get('name', '')
    logger.debug(f"歌曲: {song_name} - {artist_name}")
    
    for platform, items in results.items():
        for item in items.get('data', []):
            item_title = item.get('title', '')
            item_artist = item.get('artist', '')

            title_similarity = SequenceMatcher(None, song_name, item_title).ratio()
            artist_similarity = SequenceMatcher(None, artist_name, item_artist).ratio()
            weighted_similarity = 0.4 * title_similarity + 0.6 * artist_similarity

            matches.append((platform, item, weighted_similarity))
            logger.debug(f"匹配: {item_title} - {item_artist} (匹配度: {weighted_similarity:.2f})")

    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches

async def sync_song(session, playlist_id, song, music_source, db_manager):
    logger.debug(f"歌曲: {song}")

    # 检查数据库中是否已存在
    if db_manager.is_song_downloaded(session, playlist_id, song['id']):
        logger.info(f"歌曲 {song['name']} 已下载，跳过")
        return None

    result = await music_source.search(song['name'], 1, "music")
    matches = find_most_similar(song, result)
    
    for platform, matched_item, similarity in matches:
        logger.info(f"尝试匹配度 {similarity:.2f} 的歌曲在平台 {platform} 上: {matched_item}")

        # 获取媒体资源连接
        media_source = await music_source.get_media_source(matched_item, 'super', platform=platform)
        logger.debug(f"媒体资源: {media_source}")
        if type(media_source.get(platform, {})) != dict:
            logger.error(f"获取资源失败")
            continue

        media_url = media_source.get(platform, {}).get('url', '')
        if media_url:
            # 下载文件
            file_path = os.path.join(get_download_dir_path(), f"{matched_item['title']}-{matched_item['artist']}.mp3")
            if download_file(media_url, file_path, song):
                return file_path
            else:
                logger.warning(f"下载失败: {matched_item}")

    return None  # 如果所有尝试都失败，返回 None

async def sync_playlists():
    # 在这里执行定时查询状态的逻辑
    status = pyncm.apis.login.GetCurrentLoginStatus()
    playlists = GetUserPlaylists(status['account']['id'])
    logger.debug(f"歌单: {playlists}")

    session = db_manager.get_session()

    for playlist in playlists['playlist']:
        logger.info(f"开始同步歌单: {playlist['name']}")

        # 检查数据库中的 trackUpdateTime
        track_update_time = db_manager.get_track_update_time(session, playlist['id'])
        if track_update_time == playlist['trackUpdateTime']:
            logger.info(f"歌单 {playlist['name']} 未更新，跳过")
            continue

        await random_delay()  # 在每次同步后调用随机延迟
        playlist_id = playlist['id']
        tracks = GetPlaylistAllTracks(playlist_id)
        all_songs_downloaded = True  # 标记是否所有歌曲都已下载

        for song in tracks['songs']:
            file_path = await sync_song(session, playlist_id, song, music_source, db_manager)
            if file_path:
                # 调用封装的元数据写入方法
                write_metadata(file_path, song)
                # 记录下载信息
                db_manager.save_song_download_info(session, playlist_id, song['id'])
            else:
                all_songs_downloaded = False
                
        # 只有在所有歌曲下载完成后才更新 playlist 的 trackUpdateTime
        if all_songs_downloaded:
            db_manager.update_playlist_track_update_time(session, playlist['id'], playlist['trackUpdateTime'])

def download_file(url, file_path, song_metadata):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"下载完成: {file_path}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return False
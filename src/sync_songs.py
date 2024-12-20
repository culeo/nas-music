import os
import requests
from loguru import logger
from src.music_source import MusicSource
from src.utilities.paths import get_download_dir_path
from src.utilities.metadata_writer import write_metadata
from difflib import SequenceMatcher
from src.utilities.db_manager import DBManager, Song
from sqlalchemy.orm import joinedload

music_source = MusicSource()


def sort_by_similar(song, results):
    matches = []

    logger.debug(f"歌曲: {song.name} - {song.artist}")

    for platform, items in results.items():
        for item in items.get("data", []):
            item_title = item.get("title", "")
            item_artist = item.get("artist", "")

            title_similarity = SequenceMatcher(None, song.name, item_title).ratio()
            artist_similarity = SequenceMatcher(None, song.artist, item_artist).ratio()
            weighted_similarity = 0.4 * title_similarity + 0.6 * artist_similarity

            matches.append((platform, item, weighted_similarity))
            logger.debug(
                f"匹配: {item_title} - {item_artist} (匹配度: {weighted_similarity:.2f})"
            )

    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


async def download_song_from_sources(sources):

    for platform, item, similarity in sources:
        logger.info(f"尝试匹配度 {similarity:.2f} 的歌曲在平台 {platform} 上: {item}")

        # 获取媒体资源连接
        media_source = await music_source.get_media_source(
            item, "super", platform=platform
        )
        logger.debug(f"媒体资源: {media_source}")

        if type(media_source.get(platform, {})) != dict:
            logger.error(f"获取资源失败")
            continue

        media_url = media_source.get(platform, {}).get("url", "")
        if media_url:
            # 下载文件
            file_path = os.path.join(
                get_download_dir_path(),
                f"{item['title']}-{item['artist']}.mp3",
            )
            if download_file(media_url, file_path, item):
                # 调用封装的元数据写入方法
                write_metadata(file_path, item)

                # 获取歌词
                lyric_path = os.path.join(
                    get_download_dir_path(),
                    f"{item['title']}-{item['artist']}.lrc",
                )
                lyric_data = (
                    (await music_source.get_lyric(item, platform=platform))
                    .get(platform, {})
                    .get("rawLrc", "")
                )
                with open(lyric_path, "w", encoding="utf-8") as f:
                    f.write(lyric_data)

                return file_path
            else:
                logger.warning(f"下载失败: {item}")

    return None  # 如果所有尝试都失败，返回 None


def download_file(url, file_path, metadata):
    try:
        # 检查文件是否已经存在
        if os.path.exists(file_path):
            logger.info(f"文件已存在，跳过下载: {file_path}")
            return True

        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"下载完成: {file_path}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return False


async def sync_songs():
    db_manager = DBManager()  # 获取单例实例
    with db_manager.session_scope() as session:
        # 使用列表推导来提取 Song 的 id 列表
        pending_song_ids = [
            song_id for (song_id,) in session.query(Song.id).filter_by(state=0).all()
        ]

    for song_id in pending_song_ids:
        logger.debug(f"正在处理歌曲 ID: {song_id}")
        with db_manager.session_scope() as session:
            song_name = session.query(Song).filter_by(id=song_id).first().name

        result = await music_source.search(song_name, 1, "music")
        with db_manager.session_scope() as session:
            song = session.query(Song).filter_by(id=song_id).first()
            sources = sort_by_similar(song, result)

        file_path = await download_song_from_sources(sources)
        if file_path:
            # 更新歌曲状态为已下载
            with db_manager.session_scope() as session:
                db_manager.update_song_state(session, song_id, 1)

    # 检查并更新 Playlist 状态
    with db_manager.session_scope() as session:
        # 只查询状态为0的 Playlist
        playlists = session.query(Playlist).filter_by(state=0).all()
        for playlist in playlists:
            # 检查该 Playlist 下是否还有未下载的歌曲
            pending_songs = (
                session.query(Song).filter_by(playlist_id=playlist.id, state=0).count()
            )
            if pending_songs == 0:
                # 如果没有未下载的歌曲，更新 Playlist 状态为已完成
                db_manager.update_playlist_state(session, playlist.raw_id, 1)

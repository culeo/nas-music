from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TPOS, TCON, COMM, TXXX, APIC
from mutagen.mp3 import MP3
from datetime import datetime
import requests
from loguru import logger


def write_metadata(file_path, metadata):
    try:
        # 打开音频文件
        audio = MP3(file_path, ID3=ID3)

        # 如果文件已经有 ID3 标签，先删除它
        if audio.tags is not None:
            audio.delete()
            audio = MP3(file_path, ID3=ID3)  # 重新加载文件以确保标签被正确删除

        # 添加新的 ID3 标签
        audio.add_tags()

        # 标题（Title）
        audio.tags.add(TIT2(encoding=3, text=metadata.get("title", "")))

        # 艺术家（Artist），多个艺术家用逗号分隔
        audio.tags.add(TPE1(encoding=3, text=metadata.get("artist", "")))

        # 专辑（Album）
        audio.tags.add(TALB(encoding=3, text=metadata.get("album", "")))

        # 下载并添加专辑封面（Album Cover）
        pic_url = metadata.get("artwork", "")
        if pic_url:
            pic_response = requests.get(pic_url)
            if pic_response.status_code == 200:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=pic_response.content,
                    )
                )

        audio.save()
        logger.info(f"写入元数据成功: {file_path}")

    except Exception as e:
        logger.error(f"写入元数据失败: {e}")

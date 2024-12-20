import asyncio
import sys
from loguru import logger
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.sync_playlists import sync_playlists  # 导入 sync_playlists 方法
from src.sync_songs import sync_songs  # 导入 sync_songs 方法
from src.music_source import MusicSource
from src.apis.playlist import router as playlist_router  # 更新导入路径
from src.apis.user import router as user_router, check_login  # 更新导入路径
from src.utilities.paths import get_log_file_path  # 仅保留使用的路径管理函数

# 配置 Loguru 日志
logger.add(get_log_file_path(), rotation="1 day", retention="7 days", level="INFO")

app = FastAPI()
scheduler = AsyncIOScheduler()  # 创建调度器实例

# 包含 playlist 和 user 路由
app.include_router(playlist_router, prefix="/api")
app.include_router(user_router, prefix="/api")


async def start_scheduler():
    await check_login()  # 等待登录完成

    async def sync_tasks():
        await sync_playlists()
        await sync_songs()

    scheduler.add_job(sync_tasks, CronTrigger(hour=12, minute=0))  # 每天中午12点执行
    scheduler.start()

    await sync_tasks()


@app.on_event("startup")
async def startup_event():
    logger.info("应用已启动")

    # 检查 MusicSource 平台是否为空
    music_source = MusicSource()
    if not music_source.platforms:
        logger.error("请先配置 music source")
        sys.exit(1)  # 终止应用启动

    # 启动异步定时任务
    asyncio.create_task(start_scheduler())

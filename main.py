import asyncio
import sys
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.apis.playlist import router as playlist_router 
from src.apis.user import router as user_router
from src.apis.third_plugin import router as third_plugin_router
from src.utilities.paths import get_log_file_path 
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.scheduler.scheduler import start_scheduler 

# 配置 Loguru 日志
logger.add(get_log_file_path(), rotation="1 day", retention="7 days", level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("应用已启动")

    # 启动异步定时任务
    asyncio.create_task(start_scheduler())
    yield
    # Shutdown code (if needed)
    # Add any shutdown logic here


app = FastAPI(lifespan=lifespan)
scheduler = AsyncIOScheduler()

app.include_router(playlist_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(third_plugin_router, prefix="/api")

# 配置静态文件目录
app.mount("/", StaticFiles(directory="dist", html=True), name="static")
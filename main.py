import os, io, qrcode
import asyncio
import base64
import time
import sys
from loguru import logger
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import pyncm
from src.utilities.paths import get_session_file_path, get_log_file_path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.sync_playlists import sync_playlists  # 导入 sync_playlists 方法
from concurrent.futures import ThreadPoolExecutor
from src.music_source import MusicSource

# 配置 Loguru 日志
logger.add(get_log_file_path(), rotation="1 day", retention="7 days", level="INFO")

app = FastAPI()
login_unikey = None  # 声明为全局变量
scheduler = AsyncIOScheduler()  # 创建调度器实例

async def check_login():
    # 在这里执行定时查询状态的逻辑
    from pyncm.apis.login import (
        GetCurrentLoginStatus,
        WriteLoginInfo,
        LoginQrcodeUnikey,
        LoginQrcodeCheck,
        GetCurrentSession, 
    )

    file_path = get_session_file_path()  # 使用路径管理函数

    if os.path.exists(file_path):
            # 读取文本文件
        with open(file_path, 'r') as file:
            content = file.read()
            pyncm.SetCurrentSession(
                pyncm.LoadSessionFromString(content)
            )
        status = GetCurrentLoginStatus()
        logger.debug(f"登录状态: {status}")
        logger.info(f"已登录({status['profile']['nickname']})")
        return

    while True:
        
        global login_unikey  # 使用全局变量
        print(login_unikey)
        if login_unikey:
            rsp = LoginQrcodeCheck(login_unikey)  # 检测扫描状态
            if rsp["code"] == 803:
                # 登录成功
                logger.success("登录成功")
                status = GetCurrentLoginStatus()
                logger.debug(f"登录状态: {status}")
                logger.info(f"已登录({status['profile']['nickname']})")

                WriteLoginInfo(status, GetCurrentSession())
                session_str = pyncm.DumpSessionAsString(GetCurrentSession())
                with open(file_path, 'w') as file:
                    file.write(session_str)
                
                return
            elif rsp["code"] == 800:
                logger.info("二维码已过期,请重新获取")
            else:
                logger.info(f"等待扫码: {rsp}")
        else:
            logger.warning("未登录，请先扫码登录：http://localhost:8000/qrcode")
        await asyncio.sleep(3)

async def start_scheduler():
    await check_login()  # 等待登录完成

    scheduler.add_job(sync_playlists, CronTrigger(hour=12, minute=0))  # 每天中午12点执行
    scheduler.start()

    await sync_playlists()

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

@app.get("/qrcode")
async def create_qrcode():
    from pyncm.apis.login import (
        LoginQrcodeUnikey,
    )

    global login_unikey  # 使用全局变量
    login_unikey = LoginQrcodeUnikey()["unikey"]  # 获取 UUID
    logger.info(f"login_unikey: {login_unikey}")

    url = f"https://music.163.com/login?codekey={login_unikey}"  
    qr = qrcode.make(url)

     # 将二维码保存到内存中的字节流
    img_byte_arr = io.BytesIO()
    qr.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # 返回二维码图像
    return StreamingResponse(img_byte_arr, media_type="image/png")

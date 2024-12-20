import os
import asyncio
import io
import qrcode
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
import pyncm
from src.utilities.paths import get_session_file_path

router = APIRouter()
login_unikey = None  # 声明为全局变量

@router.get("/qrcode")
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
            logger.warning("未登录，请先扫码登录：http://localhost:8000/api/qrcode")
        await asyncio.sleep(3) 
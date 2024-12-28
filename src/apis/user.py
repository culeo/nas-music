from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
import pyncm
from datetime import timedelta
from pydantic import BaseModel
from src.crud.user import UserCRUD
from src.crud.user_preference import UserPreferenceCRUD
from src.db.session import SessionLocal
from src.schemas.user_preference import NCM_SESSION, NCM_USERNAME
from src.utilities.auth import (
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
user_crud = UserCRUD()
user_preference_crud = UserPreferenceCRUD()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    username: str
    password: str 
@router.post("/auth/login")
async def login_for_access_token(login_request: LoginRequest, db: SessionLocal = Depends(get_db)):
    logger.info(f"用户 {login_request.username} 正在登录")
    if not user_crud.verify_password(db=db, username=login_request.username, password=login_request.password):
        raise HTTPException(
            status_code=400, detail={"code": 10003, "message": "用户名或密码错误"}
        )
    user = user_crud.get_user_by_username(db=db, username=login_request.username)
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"uid": user.id}, expires_delta=access_token_expires
    )
    return {"code": 0, "message": "ok", "data": { "accessToken": access_token }}

@router.get("/auth/codes")
async def get_user_codes(current_user: str = Depends(get_current_user)):
    logger.info(f"用户 {current_user} 请求获取代码")
    # 假设用户验证通过，返回代码列表
    return {"code": 0, "message": "ok", "data": ["AC_100100", "AC_100110", "AC_100120", "AC_100010"]}

@router.get("/user/info")
async def get_user_info(uid: str = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    logger.info(f"用户 {uid} 请求用户信息")
    user = user_crud.get_user(db=db, user_id=uid)
    return {
        "code": 0,
        "message": "ok",
        "data": user
    }

@router.post("/auth/refresh")
async def refresh_access_token(uid: str = Depends(get_current_user)):
    logger.info(f"用户 {uid} 请求刷新令牌")
    
    access_token_expires = timedelta(hours==ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"uid": uid}, expires_delta=access_token_expires
    )
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "accessToken": new_access_token
        }
    }

@router.post("/auth/logout")
async def logout(uid: str = Depends(get_current_user)):
    logger.info(f"用户 {uid} 请求注销")
   
    return {
        "code": 0,
        "message": "ok",
        "data": "User logged out successfully"
    }

@router.get("/ncm/login/qrcode/unikey")
async def getNCMLoginQrcodeUnikey():
    from pyncm.apis.login import (
        LoginQrcodeUnikey,
    )

    global login_unikey  # 使用全局变量
    login_unikey = LoginQrcodeUnikey()["unikey"]  # 获取 UUID
    logger.info(f"login_unikey: {login_unikey}")

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "unikey": login_unikey
        }
    }

@router.get("/ncm/login/qrcode/check")
async def checkNCMLoginQrcodeResult(
    unikey: str = Query(), 
    uid: str = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    # 在这里执行定时查询状态的逻辑
    from pyncm.apis.login import (
        GetCurrentLoginStatus,
        WriteLoginInfo,
        LoginQrcodeCheck,
        GetCurrentSession, 
    )
    rsp = LoginQrcodeCheck(unikey)

    if rsp["code"] == 803:
        status = GetCurrentLoginStatus()
        ncm_username = status['profile']['nickname']
        logger.debug(f"登录状态: {status}")
        logger.info(f"已登录({status['profile']['nickname']})")
        WriteLoginInfo(status, GetCurrentSession())
        session_str = pyncm.DumpSessionAsString(GetCurrentSession())
        user_preference_crud.save_user_preference(db, uid, NCM_SESSION, session_str)
        user_preference_crud.save_user_preference(db, uid, NCM_USERNAME, ncm_username)
        return {
            "code": 0,
            "message": "登录成功",
            "data": { "ncm_username": ncm_username }
        }
    elif rsp["code"] == 800:
        logger.info("二维码已过期,请重新获取")
        return {
            "code": 10001,
            "message": "二维码已过期,请重新获取",
            "data": {}
        }
    else:
        logger.info(f"等待扫码: {rsp}")
        return {
            "code": 10002,
            "message": "等待扫码",
            "data": {}
        }

@router.post("/ncm/logout")
async def logout_ncm(uid: str = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    logger.info(f"用户 {uid} 请求注销")
    user_preference_crud.delete_user_preference(db = db, user_id = uid, key = NCM_SESSION)
    user_preference_crud.delete_user_preference(db = db, user_id = uid, key = NCM_USERNAME)
    return {
        "code": 0,
        "message": "ok",
        "data": "User logged out successfully"
    }   
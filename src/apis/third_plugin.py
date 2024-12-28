from fastapi import APIRouter, UploadFile, File
import httpx, os
from src.utilities.paths import get_third_plugins_dir_path
from loguru import logger
from pydantic import BaseModel

from src.utilities.third_plugins import ThirdPlugins

router = APIRouter()
third_plugins = ThirdPlugins()

@router.get("/plugin/list")
async def get_plugin_list():
    plugins = []
    for plugin in os.listdir(get_third_plugins_dir_path()):
        if plugin.endswith(".js"):
            plugins.append({"name": plugin})
    return {
        "code": 0,
        "data": {
            "items": plugins
        }
    }
    
@router.delete("/plugin/{plugin_name}")
async def delete_plugin(plugin_name: str):
    plugin_path = os.path.join(get_third_plugins_dir_path(), plugin_name)
    if os.path.exists(plugin_path):
        os.remove(plugin_path)
        return {
            "code": 0,
            "message": "ok",
            "data": {}
        }
    else:
        return {
            "code": 9999,
            "message": "插件不存在"
        }

@router.post("/plugin/upload")
async def upload_file(file: UploadFile = File(...)):
    # 验证文件类型
    if file.content_type != "text/javascript" or not file.filename.endswith(".js"):
        return {
           "code": 9999,
           "message": f"仅支持JS文件{file.content_type}"
        }

    file_location = os.path.join(get_third_plugins_dir_path(), file.filename)
    # 保存文件
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    third_plugins.reload_plugins()

    return {
        "code": 0,
        "message": "ok",
        "data": {}
    }

class PluginImportRequest(BaseModel):
    url: str
@router.post("/plugin/batch/import")
async def batch_import_third_plugin(request: PluginImportRequest):
    logger.debug(f"导入插件: {request.url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(request.url)
    try:
        data = response.json()
        print(data)
        for item in data["plugins"]:
            url = item['url']
            if url.startswith("http"):
                async with httpx.AsyncClient() as client:
                    file = await client.get(url)
                with open(os.path.join(get_third_plugins_dir_path(), f"{url.split('/')[-1]}"), "wb") as f:
                    f.write(file.content)
                    logger.info(f"导入插件成功: {url}")
        third_plugins.reload_plugins()
        return {
            "code": 0,
            "message": "ok",
            "data": "ok"
        }  
    except Exception as e:
        logger.error(f"导入插件失败: {e}")
        return {
           "code": 9999,
           "message": f"导入插件失败: {e}"
        }


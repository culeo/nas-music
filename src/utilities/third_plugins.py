import json
import subprocess
import os
from src.utilities.tools import random_delay  # 导入 random_delay 方法
from src.utilities.paths import get_third_plugins_dir_path
from loguru import logger

class ThirdPlugins:
    def __init__(self):
        self.plugins = self._load_plugins(get_third_plugins_dir_path())

    def _load_plugins(self, plugins_dir):
        plugins = {}
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".js"):
                file_path = os.path.join(plugins_dir, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    try:
                        start = content.index('platform: "') + len('platform: "')
                        end = content.index('"', start)
                        plugin_name = content[start:end]
                        plugins[plugin_name] = file_path
                    except ValueError:
                        plugins[filename] = "未找到平台名称"
        return plugins

    async def _call_js_function(self, function_name, *args, plugin: str) -> dict:
        js_file_path = self.plugins.get(plugin)
        if not js_file_path:
            return {}
        try:
            args_json = json.dumps(args)
            result = subprocess.run(
                [
                    "node",
                    "-e",
                    f"""
                    const {{ {function_name} }} = require('{js_file_path}');
                    {function_name}(...{args_json}).then(result => {{
                        console.log(JSON.stringify(result));
                    }}).catch(error => {{
                        console.error(error);
                        process.exit(1);
                    }});
                """,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
            else:
                logger.error(f"调用 Node.js 出错: {result.stderr}")
                return {}
        except Exception as e:
            logger.error(f"调用 Node.js 出错: {e}")
            return {}
    def reload_plugins(self):
        self.plugins = self._load_plugins(get_third_plugins_dir_path())

    async def search(self, query: str, page: int, type: str, plugins: list|None = None) -> dict:
        if plugins is None:
            plugins = self.plugins
        if len(plugins) == 0:
            logger.error("没有可用插件")
            return
        for plugin in plugins:
            result = await self._call_js_function("search", query, page, type, plugin=plugin)
            if len(result) > 0:
                yield plugin, result

    async def get_media_source(self, music_item: dict, quality: str, plugin: str):
        return await self._call_js_function("getMediaSource", music_item, quality, plugin=plugin)

    async def get_lyric(self, music_item: dict, plugin: str):
        return await self._call_js_function("getLyric", music_item, plugin=plugin)

    async def get_album_info(self, *args, plugin: str):
        return await self._call_js_function("getAlbumInfo", *args, plugin=plugin)

    async def get_artist_works(self, *args, plugin: str):
        return await self._call_js_function("getArtistWorks", *args, plugin=plugin)

    async def import_music_sheet(self, *args, plugin: str):
        return await self._call_js_function("importMusicSheet", *args, plugin=plugin)

    async def get_top_lists(self, plugin: str):
        return await self._call_js_function("getTopLists", plugin=plugin)

    async def get_top_list_detail(self, *args, plugin: str):
        return await self._call_js_function("getTopListDetail", *args, plugin=plugin)

    async def get_recommend_sheet_tags(self, plugin: str):
        return await self._call_js_function("getRecommendSheetTags", plugin=plugin)

    async def get_recommend_sheets_by_tag(self, *args, plugin: str):
        return await self._call_js_function(
            "getRecommendSheetsByTag", *args, plugin=plugin
        )

    async def get_music_sheet_info(self, *args, plugin: str):
        return await self._call_js_function("getMusicSheetInfo", *args, plugin=plugin)

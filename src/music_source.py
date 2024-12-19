import json
import subprocess
import os
from src.utilities.tools import random_delay  # 导入 random_delay 方法
from src.utilities.paths import get_music_source_dir_path

class MusicSource:
    def __init__(self):
        self.platforms = self._load_platforms(get_music_source_dir_path())

    def _load_platforms(self, source_dir):
        platforms = {}
        for filename in os.listdir(source_dir):
            if filename.endswith('.js'):
                file_path = os.path.join(source_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    try:
                        start = content.index('platform: "') + len('platform: "')
                        end = content.index('"', start)
                        platform_name = content[start:end]
                        platforms[platform_name] = file_path
                    except ValueError:
                        platforms[filename] = "未找到平台名称"
        return platforms

    async def _call_js_function(self, function_name, *args, platform=None):
        results = {}
        target_platforms = [platform] if platform else self.platforms.keys()

        for platform_name in target_platforms:
            js_file_path = self.platforms.get(platform_name)
            if not js_file_path:
                continue
                    
            try:
                args_json = json.dumps(args)
                result = subprocess.run(
                    ['node', '-e', f"""
                        const {{ {function_name} }} = require('{js_file_path}');
                        {function_name}(...{args_json}).then(result => {{
                            console.log(JSON.stringify(result));
                        }}).catch(error => {{
                            console.error(error);
                            process.exit(1);
                        }});
                    """],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout:
                    results[platform_name] = json.loads(result.stdout)
                else:
                    results[platform_name] = f"Node.js Error: {result.stderr}"
                    
            except Exception as e:
                results[platform_name] = f"Error: {str(e)}"
            
            # 在每次调用后添加随机延迟
            await random_delay()
        
        return results

    def search(self, query: str, page: int, type: str, platform=None):
        return self._call_js_function('search', query, page, type, platform=platform)
        
    def get_media_source(self, music_item: dict, quality: str, platform=None):
        return self._call_js_function('getMediaSource', music_item, quality, platform=platform)

    def get_lyric(self, *args, platform=None):
        return self._call_js_function('getLyric', *args, platform=platform)

    def get_album_info(self, *args, platform=None):
        return self._call_js_function('getAlbumInfo', *args, platform=platform)

    def get_artist_works(self, *args, platform=None):
        return self._call_js_function('getArtistWorks', *args, platform=platform)

    def import_music_sheet(self, *args, platform=None):
        return self._call_js_function('importMusicSheet', *args, platform=platform)

    def get_top_lists(self, platform=None):
        return self._call_js_function('getTopLists', platform=platform)

    def get_top_list_detail(self, *args, platform=None):
        return self._call_js_function('getTopListDetail', *args, platform=platform)

    def get_recommend_sheet_tags(self, platform=None):
        return self._call_js_function('getRecommendSheetTags', platform=platform)

    def get_recommend_sheets_by_tag(self, *args, platform=None):
        return self._call_js_function('getRecommendSheetsByTag', *args, platform=platform)

    def get_music_sheet_info(self, *args, platform=None):
        return self._call_js_function('getMusicSheetInfo', *args, platform=platform)


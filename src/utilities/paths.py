import os

def get_log_file_path():
    log_dir = './cache/logs'
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'app_{time}.log')

def get_data_dir_path():
    data_dir = os.getenv('DATA_PATH', './cache/data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_music_source_dir_path():
    music_source_dir = os.path.join(get_data_dir_path(), 'music_source')
    os.makedirs(music_source_dir, exist_ok=True)
    return music_source_dir

def get_session_file_path():
    # 定义缓存目录
    # 确保目录存在
    file_path = os.path.join(get_data_dir_path(), 'session.txt')
    # 返回完整的文件路径
    return file_path

def get_database_file_path():
    # 定义数据目录
    file_path = os.path.join(get_data_dir_path(), 'nas-music-v2.db')
    # 返回完整的数据库文件路径
    return file_path

def get_download_dir_path(): 
    download_dir = os.getenv('DOWNLOAD_PATH', './cache/downloads')
    os.makedirs(download_dir, exist_ok=True)
    return download_dir

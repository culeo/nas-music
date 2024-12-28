import os
def get_log_file_path():
    log_dir = './cache/logs'
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'app_{time}.log')

def get_data_dir_path():
    data_dir = os.getenv('DATA_PATH', './cache/data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_third_plugins_dir_path():
    third_plugins_dir = os.path.join(get_data_dir_path(), 'third_plugins')
    os.makedirs(third_plugins_dir, exist_ok=True)
    return third_plugins_dir

def get_database_file_path():
    # 定义数据目录
    file_path = os.path.join(get_data_dir_path(), 'nas-music-v2.db')
    # 返回完整的数据库文件路径
    return file_path

def get_download_dir_path(): 
    download_dir = os.getenv('DOWNLOAD_PATH', './cache/downloads')
    os.makedirs(download_dir, exist_ok=True)
    return download_dir

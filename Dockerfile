# 使用官方的 Python 3.11.10 镜像作为基础镜像
FROM python:3.11.10-slim

# 安装 Node.js v18.20.4
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs=18.20.4-1nodesource1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY ./package.json ./requirements.txt ./main.py ./
COPY ./src ./src 

# 安装 Node.js 依赖
RUN npm install

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露应用运行的端口
EXPOSE 8000

ENV DATA_PATH=/app/data
ENV DOWNLOAD_PATH=/downloads

# 添加可执行权限
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
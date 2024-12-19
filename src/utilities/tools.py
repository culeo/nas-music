import asyncio
import random
from loguru import logger

async def random_delay():
    delay = random.randint(1, 10)  # 生成1到10之间的随机整数
    logger.info(f"随机延迟 {delay} 秒")
    await asyncio.sleep(delay)  # 异步延迟 
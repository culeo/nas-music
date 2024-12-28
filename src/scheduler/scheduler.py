from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.scheduler.tasks.sync_playlists_task import sync_playlists_task
from datetime import datetime
from src.utilities.tools import random_delay

scheduler = AsyncIOScheduler()

async def trigger_sync_playlists_task():
    await random_delay()
    try:
        job = scheduler.get_job("sync_playlists")
        if job:
            job.modify(next_run_time=datetime.now())
    except Exception as e:
        print(f"Error while triggering task: {e}")

async def start_scheduler():
    scheduler.add_job(sync_playlists_task, id="sync_playlists", trigger=CronTrigger.from_crontab("0 12 * * *"), max_instances=1)  # 限制最大并发为1
    scheduler.start()

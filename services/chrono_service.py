import time
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List

import schedule

from services.tasks.backup_db_task import BackupDatabaseTask
from services.tasks.chrono_task import ChronoTask
from services.tasks.log_file_task import LogFileTask

class ChronoService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.tasks: List[ChronoTask] = [LogFileTask(), BackupDatabaseTask()]

    def run_threaded(self, func):
        self.executor.submit(func)

    def execute(self):
        for task in self.tasks:
            schedule.every(task.interval).minutes.do(self.run_threaded, task.execute)
        while True:
            schedule.run_pending()
            time.sleep(60)
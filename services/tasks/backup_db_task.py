import logging
import os

from services.tasks.chrono_task import ChronoTask
from settings.chrono_task_settings import DB_BACKUP_FREQUENCY
from settings.settings import DB_NAME
from shutil import copyfile

class BackupDatabaseTask(ChronoTask):
    def __init__(self):
        super().__init__(DB_BACKUP_FREQUENCY)

    def execute(self):
        if os.path.exists(DB_NAME):
            if not os.path.exists("db_backup"):
                os.makedirs("db_backup")

            time_formatted = ChronoTask.format_time()

            for i in range(1, 5):
                try:
                    copyfile(DB_NAME, f"db_backup/backup_{time_formatted}.db")
                    logging.info("Successfully backed up database")
                    return
                except Exception as e:
                    logging.error("Error while copying db file")

            logging.error("There was an error while backing up database")
import logging
import os

from services.tasks.chrono_task import ChronoTask
from settings.chrono_task_settings import LOG_REPLACEMENT_FREQUENCY

class LogFileTask(ChronoTask):
    def __init__(self):
        super().__init__(LOG_REPLACEMENT_FREQUENCY)

    def execute(self):
        LogFileTask.create_new_logger()

    @staticmethod
    def create_new_logger():
        logging.info("Creating a new logger")
        time_formatted = ChronoTask.format_time()
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(module)s - %(funcName)s: %(message)s", '%Y-%m-%d %H:%M:%S')

        if not os.path.exists("logs"):
            os.makedirs("logs")
        file_handler = logging.FileHandler(f"logs/debug{time_formatted}.log", mode="w")
        file_handler.setLevel(logging.WARNING)
        file_handler.formatter = formatter

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)
        logger.addHandler(file_handler)

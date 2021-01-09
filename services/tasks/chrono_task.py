import time


class ChronoTask:
    # interval is in minutes
    def __init__(self, interval):
        self.interval = interval

    def execute(self):
        raise Exception("Execute for task not implemented")

    @staticmethod
    def format_time():
        return time.strftime('%Y%m%d-%H%M')
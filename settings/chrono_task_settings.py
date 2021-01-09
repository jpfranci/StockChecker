from dotenv import load_dotenv
import os

from conversions.time_conversions import hours_to_minutes

load_dotenv()

# time (in minutes) of frequency of chrono tasks
LOG_REPLACEMENT_FREQUENCY = hours_to_minutes(float(os.getenv("LOG_REPLACEMENT_FREQUENCY", 24)))
DB_BACKUP_FREQUENCY = hours_to_minutes(float(os.getenv("DB_BACKUP_FREQUENCY", 24)))
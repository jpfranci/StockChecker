import os
import json
from dotenv import load_dotenv

load_dotenv()
WEBDRIVER_URI = os.getenv("WEBDRIVER_URI")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BROADCAST_CHANNEL = os.getenv("BROADCAST_CHANNEL")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# time in between stock checks (in seconds) for items
SELENIUM_TIME_THRESHOLD = int(os.getenv("SELENIUM_TIME_THRESHOLD"))
REQUESTS_TIME_THRESHOLD = int(os.getenv("REQUESTS_TIME_THRESHOLD"))

# time (in seconds) between creating new selenium browser
SELENIUM_CREATE_NEW_BROWSER_INTERVAL = int(os.getenv("SELENIUM_CREATE_NEW_BROWSER_INTERVAL"))

# time (in seconds) between stock checks for items when the previous check has failed
OFFSET_BETWEEN_FAILS = int(os.getenv("OFFSET_BETWEEN_FAILS"))
ADMINISTRATOR_ID = int(os.getenv("ADMINISTRATOR_ID"))
IS_LOCAL = os.getenv("IS_LOCAL", "True") == "True"

# dict representing override of SELENIUM_TIME_THRESHOLD or REQUESTS_TIME_THRESHOLD, to set intervals between stock checks longer for that website
# if empty for a given website, the default will be used
TIME_THRESHOLD_OVERRIDE_DICT = {}
try:
    TIME_THRESHOLD_OVERRIDE_DICT = json.loads(os.getenv("TIME_THRESHOLD_OVERRIDE_DICT"))
except:
    print("No time threshold overrides given for any websites")

ADDITIONAL_USERS_TO_PING = []
try:
    ADDITIONAL_USERS_TO_PING = json.loads(os.getenv("ADDITIONAL_USERS_TO_PING"))
except:
    print("No additional users to ping directly")
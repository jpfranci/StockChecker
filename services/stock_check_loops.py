import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import sql_item_persistence
import stock_check_result_reporter
from model import website
from model.website import time_threshold_dict
from services import user_agent_service
from settings.settings import SELENIUM_TIME_THRESHOLD, OFFSET_BETWEEN_FAILS, SELENIUM_CREATE_NEW_BROWSER_INTERVAL, \
    IS_LOCAL, WEBDRIVER_URI, REQUESTS_TIME_THRESHOLD
from stock_checkers.stock_check_result import StockCheckResult

class StockCheckLoops:
    def __init__(self, bot):
        self.bot = bot

    def run_selenium_stock_loop(self, main_thread_loop):
        last_driver_time = datetime.fromtimestamp(0)
        driver = None

        persistence = sql_item_persistence.sqlite_item_persistence
        conn = sql_item_persistence.sqlite_item_persistence.get_connection()
        websites_to_process = list(map(lambda x: x.value, list(website.selenium_website_dict.keys())))

        while True:
            try:
                driver, last_driver_time = self.create_webdriver_if_needed(driver, last_driver_time)
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)
                break
            try:
                items = persistence.get_items(conn, int((datetime.now(tz=timezone.utc) - timedelta(seconds = SELENIUM_TIME_THRESHOLD)).timestamp()), websites_to_process)
                if items:
                    for item in items:
                        if self.should_check_item(item):
                            logging.info(f"Checking stock for {item.url}")
                            driver.get(item.url)
                            stock_result: StockCheckResult = website.selenium_website_dict[item.website].check_stock(driver, item.url)
                            stock_result.format_log()
                            stock_check_result_reporter.handle_stock_check_result(conn, stock_result, item, main_thread_loop, datetime.now(tz=timezone.utc), self.bot)
                            time.sleep(5)
                    time.sleep(5)
                else:
                    time.sleep(10)
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)

    @staticmethod
    def should_check_item(item) -> bool:
        return item.last_stock_check + timedelta(seconds=time_threshold_dict[item.website]) < datetime.now(tz=timezone.utc) and \
               (item.last_stock_check_result is None or
                item.last_stock_check_result.fail_count == 0 or
                item.last_stock_check + timedelta(seconds=OFFSET_BETWEEN_FAILS) <= datetime.now(tz=timezone.utc))

    @staticmethod
    def create_webdriver_if_needed(driver, last_driver_time):
        if driver is None or last_driver_time + timedelta(seconds=SELENIUM_CREATE_NEW_BROWSER_INTERVAL) < datetime.now(tz = timezone.utc):
            if driver is not None:
                driver.quit()
            chrome_options = Options()
            user_agent = user_agent_service.get_chrome_user_agent()
            if user_agent != "":
                chrome_options.add_argument(f'user-agent={user_agent}')
            if not IS_LOCAL:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--log-level=3")
            logging.info(f"Creating chrome webdriver with user agent {user_agent}")
            driver = webdriver.Chrome(WEBDRIVER_URI, options = chrome_options)
            last_driver_time = datetime.now(tz=timezone.utc)
        return driver, last_driver_time

    def run_request_stock_loop(self, main_thread_loop):
        request_loop = asyncio.new_event_loop()
        request_loop.run_until_complete(self.request_stock_loop(main_thread_loop))

    async def request_stock_loop(self, main_thread_loop):
        persistence = sql_item_persistence.sqlite_item_persistence
        conn = sql_item_persistence.sqlite_item_persistence.get_connection()
        websites_to_process = list(map(lambda x: x.value, list(website.requests_website_dict.keys())))
        while True:
            try:
                items = persistence.get_items(conn, int((datetime.now(tz=timezone.utc) - timedelta(seconds=REQUESTS_TIME_THRESHOLD)).timestamp()), websites_to_process)
                tasks = []
                items_dict = {}

                for item in items:
                    if self.should_check_item(item):
                        logging.info(f"Checking stock for {item.url}")
                        items_dict[item.url] = item
                        tasks.append(website.requests_website_dict[item.website].check_stock(item.url))

                stock_check_results = await asyncio.gather(*tasks)
                stock_check_time = datetime.now(tz=timezone.utc)
                for stock_check_result in stock_check_results:
                    stock_check_result.format_log()
                    item = items_dict[stock_check_result.item_url]
                    stock_check_result_reporter.handle_stock_check_result(conn, stock_check_result, item, main_thread_loop, stock_check_time, self.bot)
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)
            time.sleep(10)
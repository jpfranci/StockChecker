import json
import logging
import traceback

from pysqlcipher3 import dbapi2 as sqlite3
from threading import Lock
from typing import Optional, List, Dict
from datetime import datetime, timezone

from model.item import Item
from model.notification_user import NotificationUser
from model.price_history import PriceHistory
from model.stock_options import StockOptions
from model.website import Website
from settings.settings import DB_PASSWORD, DB_NAME
from stock_checkers.stock_check_result import StockCheckResult

sql_create_items_table = """ CREATE TABLE IF NOT EXISTS items (
    item_url text PRIMARY KEY,
    website text NOT NULL,
    stock_status integer NOT NULL,
    last_stock_check integer NOT NULL,
    item_name text NOT NULL,
    last_stock_check_result text 
);
"""

sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
    id integer NOT NULL,
    stock_options text NOT NULL,
    last_stock_status integer NOT NULL,
    item_url text NOT NULL,
    item_name text,
    last_in_stock_sizes text NOT NULL,
    last_in_stock_stores text NOT NULL,
    PRIMARY KEY(id, item_url) 
    FOREIGN KEY(item_url) REFERENCES items(item_url)
);
"""

sql_create_price_history_table = """ CREATE TABLE IF NOT EXISTS price_history (
    item_url text NOT NULL,
    stock_check_time int NOT NULL,
    stock_check_result text NOT NULL,
    PRIMARY KEY(item_url, stock_check_time),
    FOREIGN KEY(item_url) REFERENCES items(item_url)
);
"""
lock = Lock()

class SqliteItemPersistence:
    def __init__(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(sql_create_items_table)
        c.execute(sql_create_users_table)
        c.execute(sql_create_price_history_table)
        conn.commit()
        conn.close()

    def get_item(self, conn, item_url: str) -> Optional[Item]:
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * from items WHERE item_url = ?", (item_url,))
            data = cursor.fetchone()
            if data is None:
                return None
            else:
                return SqliteItemPersistence.to_item(data)
        finally:
            lock.release()

    def get_items(self, conn, stock_check_threshold: int, websites: List[str]):
        lock.acquire()
        try:
            cursor = conn.cursor()
            if websites:
                websites_param = SqliteItemPersistence.get_prepared_str(websites)
                query = f"SELECT * from items WHERE last_stock_check <= ? AND website IN ({websites_param}) AND EXISTS (SELECT 1 FROM users WHERE items.item_url = item_url)"
                cursor.execute(query, (stock_check_threshold, *websites))
                data = cursor.fetchall()
                return list(map(SqliteItemPersistence.to_item, data))
            else:
                return []
        finally:
            lock.release()

    @staticmethod
    def get_prepared_str(elements):
        return ",".join("?"*len(elements))

    def delete_notification_user(self, conn, id, item_url):
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE from users WHERE users.id = ? and users.item_url = ?", (id, item_url))
            conn.commit()
        finally:
            lock.release()

    def delete_all_notification_users_with_id(self, conn, id: int):
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE from users WHERE users.id = ?", (id,))
            conn.commit()
        finally:
            lock.release()

    def get_all_subscribed_for_user(self, conn, id) -> List[NotificationUser]:
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * from users WHERE id = ?", (id,))
            data = cursor.fetchall()
            return list(map(SqliteItemPersistence.to_user, data))
        finally:
            lock.release()

    def get_latest_price_histories(self, conn, item_urls: List[str], max_to_retrieve: int) -> Dict[str, List[PriceHistory]]:
        lock.acquire()
        try:
            cursor = conn.cursor()
            item_urls_statement = SqliteItemPersistence.get_prepared_str(item_urls)
            cursor.execute(f"SELECT * from price_history WHERE item_url IN ({item_urls_statement}) ORDER BY stock_check_time DESC", item_urls)
            data = cursor.fetchall()
            all_price_histories = map(SqliteItemPersistence.to_price_history, data)

            url_to_price_dict = {}
            for price_history in all_price_histories:
                item_url = price_history.stock_check_result.item_url
                if item_url in url_to_price_dict:
                    top_price_histories = url_to_price_dict[item_url]
                    if len(top_price_histories) < max_to_retrieve:
                        top_price_histories.append(price_history)
                else:
                    url_to_price_dict[item_url] = [price_history]

            return url_to_price_dict
        finally:
            lock.release()

    def upsert_item(self, conn, item: Item):
        lock.acquire()
        try:
            cursor = conn.cursor()
            last_stock_check_result = None if item.last_stock_check_result is None else item.last_stock_check_result.to_json()
            values_to_insert = (item.url, item.website.value, int(item.stock_status), int(item.last_stock_check.timestamp()), item.item_name, last_stock_check_result)
            cursor.execute("REPLACE INTO items VALUES (?, ?, ?, ?, ?, ?)", values_to_insert)
            conn.commit()
        finally:
            lock.release()

    def insert_price_history(self, conn, stock_check_result: StockCheckResult, stock_check_time: int):
        lock.acquire()
        try:
            cursor = conn.cursor()
            values_to_insert = (stock_check_result.item_url, stock_check_time, stock_check_result.to_json())
            cursor.execute("INSERT OR IGNORE INTO price_history VALUES (?, ?, ?)", values_to_insert)
            conn.commit()
        finally:
            lock.release()

    def insert_item_if_doesnt_exist(self, conn, item: Item):
        lock.acquire()
        try:
            cursor = conn.cursor()
            last_stock_check_result = None if item.last_stock_check_result is None else item.last_stock_check_result.to_json()
            values_to_insert = (item.url, item.website.value, int(item.stock_status), int(item.last_stock_check.timestamp()), item.item_name, last_stock_check_result)
            cursor.execute("INSERT OR IGNORE INTO items VALUES (?, ?, ?, ?, ?, ?)", values_to_insert)
            conn.commit()
        finally:
            lock.release()

    def update_stock_check_time(self, conn, item_url: str, new_stock_check_time: int):
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE item SET last_stock_check = ? WHERE item_url = ?", (new_stock_check_time, item_url))
            conn.commit()
        finally:
            lock.release()

    def upsert_notification_user(self, conn, notification_user: NotificationUser):
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (notification_user.id,
                            json.dumps(notification_user.stock_options.__dict__),
                            int(notification_user.last_stock_status),
                            notification_user.item_url,
                            notification_user.item_name,
                            json.dumps(list(notification_user.last_in_stock_sizes_for_user)),
                            json.dumps(list(notification_user.last_in_stock_stores_for_user))))
            conn.commit()
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
        finally:
            lock.release()

    def get_subscribed_users_for_item(self, conn, item: Item):
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * from users WHERE item_url = ?", (item.url,))
            data = cursor.fetchall()
            return list(map(SqliteItemPersistence.to_user, data))
        finally:
            lock.release()

    def get_notification_user(self, conn, id: int, item_url) -> Optional[NotificationUser]:
        lock.acquire()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * from users WHERE id = ? and item_url = ?", (id, item_url,))
            data = cursor.fetchone()
            if data is not None:
                return SqliteItemPersistence.to_user(data)
            else:
                return None
        finally:
            lock.release()

    def get_connection(self):
        lock.acquire()
        try:
            conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA key = '{DB_PASSWORD}'")
            return conn
        finally:
            lock.release()

    def does_item_exist(self, conn, item_url: str):
        return self.get_item(conn, item_url) is not None

    @staticmethod
    def to_item(data) -> Item:
        return Item(
            data[0],
            Website(data[1]),
            bool(data[2]),
            datetime.fromtimestamp(data[3], tz=timezone.utc),
            data[4],
            None if data[5] is None else StockCheckResult.from_json(json.loads(data[5])))

    @staticmethod
    def to_user(data) -> NotificationUser:
        last_in_stock_stores = [] if not data[6] else json.loads(data[6])
        return NotificationUser(
            data[0],
            StockOptions.from_json(json.loads(data[1])),
            bool(data[2]),
            data[3],
            data[4],
            json.loads(data[5]),
            last_in_stock_stores)

    @staticmethod
    def to_price_history(data) -> PriceHistory:
        return PriceHistory(
            StockCheckResult.from_json(json.loads(data[2])),
            datetime.fromtimestamp(data[1], tz=timezone.utc))

sqlite_item_persistence = SqliteItemPersistence()

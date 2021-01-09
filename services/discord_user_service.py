import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Dict

from model.item import Item
from model.price_history import PriceHistory
from model.user_exception import UserException
from model.website import Website, website_dict
from model.notification_user import NotificationUser
from datetime import datetime, timezone

from sql_item_persistence import sqlite_item_persistence

discord_executor = ThreadPoolExecutor(max_workers=5)
async def subscribe(user: NotificationUser, item_url: str, website: Website) -> Item:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(discord_executor, subscribe_sync, user, item_url, website, loop)

def subscribe_sync(user: NotificationUser, item_url: str, website: Website, loop) -> Item:
    conn = sqlite_item_persistence.get_connection()
    try:
        item = sqlite_item_persistence.get_item(conn, item_url)
        if item is not None:
            user.item_name = item.item_name
            sqlite_item_persistence.upsert_notification_user(conn, user)
        else:
            item_name_future = asyncio.run_coroutine_threadsafe(website_dict[website].get_item_name_from_url(item_url, discord_executor), loop)
            item = create_item(item_url, item_name_future.result(), website)
            sqlite_item_persistence.insert_item_if_doesnt_exist(conn, item)
            user.item_name = item.item_name
            sqlite_item_persistence.upsert_notification_user(conn, user)
    finally:
        conn.close()
    return item

async def unsubscribe(item_url: str, user: NotificationUser):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(discord_executor, unsubscribe_sync, item_url, user)

def unsubscribe_sync(item_url: str, user: NotificationUser):
    conn = sqlite_item_persistence.get_connection()
    try:
        if sqlite_item_persistence.does_item_exist(conn, item_url):
            sqlite_item_persistence.delete_notification_user(conn, user.id, item_url)
        else:
            raise UserException(f"You are not currently subscribed to {item_url}")
    finally:
        conn.close()

def upsert_user_sync(notification_user: NotificationUser):
    conn = sqlite_item_persistence.get_connection()
    try:
        sqlite_item_persistence.upsert_notification_user(conn, notification_user)
    finally:
        conn.close()

async def upsert_user(notification_user: NotificationUser):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(discord_executor, upsert_user_sync, notification_user)

def get_all_subscribed_for_user_sync(user_id: int) -> List[NotificationUser]:
    conn = sqlite_item_persistence.get_connection()
    try:
        notification_users = sqlite_item_persistence.get_all_subscribed_for_user(conn, user_id)
    finally:
        conn.close()
    return notification_users

async def get_all_subscribed_for_user(user_id: int) -> List[NotificationUser]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(discord_executor, get_all_subscribed_for_user_sync, user_id)

def get_latest_prices_histories_sync(item_urls: List[str], max_to_retrieve: int) -> Dict[str, List[PriceHistory]]:
    conn = sqlite_item_persistence.get_connection()
    try:
        price_histories = sqlite_item_persistence.get_latest_price_histories(conn, item_urls, max_to_retrieve)
    finally:
        conn.close()
    return price_histories

async def get_latest_price_histories(item_urls: List[str], max_to_retrieve: int) -> Dict[str, List[PriceHistory]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(discord_executor, get_latest_prices_histories_sync, item_urls, max_to_retrieve)

def unsubscribe_all_sync(id: int):
    conn = sqlite_item_persistence.get_connection()
    try:
        sqlite_item_persistence.delete_all_notification_users_with_id(conn, id)
    finally:
        conn.close()

async def unsubscribe_all(id: int):
    loop = asyncio.get_event_loop()
    currently_subscribed = await get_all_subscribed_for_user(id)
    if currently_subscribed:
        await loop.run_in_executor(discord_executor, unsubscribe_all_sync, id)
    else:
        raise UserException("You are not currently subscribed to anything")

def create_item(item_url: str, item_name: str, website: Website):
    return Item(
        item_url,
        website,
        False,
        datetime.fromtimestamp(0, tz=timezone.utc),
        item_name,
        None)
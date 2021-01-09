import asyncio
import logging
import math
import traceback
from typing import List, Set
from datetime import datetime

import tldextract

from services import discord_user_service
import sql_item_persistence
from conversions.message_formatters import chunk_messages
from conversions.size_formatters import get_size_requirement_str
from model.item import Item
from model.notification_user import NotificationUser
from model.website import Website, bannable_websites
from settings.settings import ADMINISTRATOR_ID
from stock_checkers.stock_check_result import StockCheckResult, MAX_FAILURES, NO_IN_STOCK_SIZES

def handle_stock_check_result(conn, stock_check_result: StockCheckResult, item: Item, main_thread_loop, stock_check_time: datetime, bot):
    item.item_name = stock_check_result.item_name if stock_check_result.item_name is not None and stock_check_result.item_name != "" else item.item_name
    item.last_stock_check = stock_check_time
    stock_check_result.item_name = item.item_name
    stock_check_result.fail_count = 0 if item.last_stock_check_result is None else item.last_stock_check_result.fail_count
    if not stock_check_result.is_item_available:
        stock_check_result.fail_count += 1
    else:
        stock_check_result.fail_count = 0

    if item.last_stock_check_result != stock_check_result:
        sql_item_persistence.sqlite_item_persistence.insert_price_history(conn, stock_check_result, int(item.last_stock_check.timestamp()))

    item.stock_status = stock_check_result.is_in_stock
    item.last_stock_check_result = stock_check_result
    sql_item_persistence.sqlite_item_persistence.upsert_item(conn, item)
    subscribed_users = sql_item_persistence.sqlite_item_persistence.get_subscribed_users_for_item(conn, item)

    for subscribed_user in subscribed_users:
        asyncio.run_coroutine_threadsafe(notify_valid_subscribers(subscribed_user, item, stock_check_result, bot), main_thread_loop)

async def send_message(user_id, message, bot):
    logging.info(f"Sending message: {message}")
    for total_fail_count in range(0, 5):
        try:
            user = bot.get_user(int(user_id))
            if user is None:
                user = await bot.fetch_user(int(user_id))
            await user.send(message)
            break
        except Exception as e:
            logging.error(e)
            logging.error(traceback.format_exc(limit=5))

async def notify_valid_subscribers(subscribed_user: NotificationUser, item: Item, stock_result: StockCheckResult, bot):
    is_unsubscribed = False
    if item.item_name != subscribed_user.item_name:
        subscribed_user.item_name = item.item_name

    if stock_result.is_item_available:
        is_unsubscribed, messages = handle_available_stock_check_result(subscribed_user, item, stock_result)
        message_chunks = chunk_messages(messages, 2)
        send_message_tasks = list(map(lambda message: send_message(subscribed_user.id, message, bot), message_chunks))
        await asyncio.gather(*send_message_tasks)
    else:
        logging.error(stock_result.format_log())
        website = Website(tldextract.extract(stock_result.item_url).domain)
        if stock_result.fail_count >= MAX_FAILURES:
            if website not in bannable_websites:
                is_unsubscribed = True
                await discord_user_service.unsubscribe(stock_result.item_url, subscribed_user)
                await send_message(subscribed_user.id, f'You have been unsubscribed from tracking {item.item_name} for {stock_result.item_url} because it may no longer be available or the bot got banned.', bot)
            elif stock_result.fail_count == MAX_FAILURES:
                await send_message(ADMINISTRATOR_ID, f'The bot has been banned from {website.value} and url {stock_result.item_url}', bot)

    if not is_unsubscribed:
        await discord_user_service.upsert_user(subscribed_user)
    else:
        await discord_user_service.unsubscribe(stock_result.item_url, subscribed_user)

def handle_available_stock_check_result(subscribed_user: NotificationUser, item: Item, stock_check_result: StockCheckResult):
    messages = []
    item_name = item.item_name
    in_stock_sizes_for_user_set = set(subscribed_user.stock_options.size_requirement).intersection(set(stock_check_result.in_stock_sizes))
    is_unsubscribed = False
    price_to_use, price_str_to_use, previous_price_to_use = get_prices_to_use(subscribed_user, stock_check_result, item)

    if should_check_size_requirement(subscribed_user.stock_options.size_requirement, stock_check_result.available_sizes):
        are_all_sizes_valid, message_portion = check_validity_of_subscribed_sizes(subscribed_user, stock_check_result)
        is_unsubscribed = not are_all_sizes_valid
        messages.append(message_portion)

    if is_stock_check_result_different_for_user(stock_check_result, subscribed_user, in_stock_sizes_for_user_set):
        if (not verify_price(subscribed_user.stock_options.price_threshold, price_to_use) or not stock_check_result.is_in_stock) and subscribed_user.last_stock_status:
            subscribed_user.last_stock_status = False
            messages.append(f'{item_name} at {item.url} just went out of stock')
        elif stock_check_result.is_in_stock:
            messages.extend(handle_valid_in_stock_result(subscribed_user, stock_check_result, item, in_stock_sizes_for_user_set))

    return is_unsubscribed, messages

def handle_valid_in_stock_result(subscribed_user: NotificationUser, stock_check_result: StockCheckResult, item: Item, in_stock_sizes_for_user_set):
    messages = []
    price_to_use, price_str_to_use, previous_price_to_use = get_prices_to_use(subscribed_user, stock_check_result, item)
    item_name = item.item_name

    if verify_price(subscribed_user.stock_options.price_threshold, price_to_use):
        messages.extend(handle_valid_price(subscribed_user, stock_check_result, in_stock_sizes_for_user_set, price_str_to_use))
        subscribed_user.set_last_in_stock_stores_for_user(stock_check_result.in_stock_stores)
        subscribed_user.set_last_in_stock_sizes_for_user(in_stock_sizes_for_user_set)
    elif is_price_over_threshold_for_first_time(subscribed_user, previous_price_to_use):
        official_sources_str = f"when sold by {item.website.value} directly" if subscribed_user.stock_options.official_sites_only else f"any seller on {item.website.value}"
        messages.extend(f'The price for {item_name} ({price_str_to_use}) {official_sources_str} at {stock_check_result.item_url} has exceeded your limit of ${subscribed_user.stock_options.price_threshold}')
        subscribed_user.set_last_in_stock_sizes_for_user([])
        subscribed_user.set_last_in_stock_stores_for_user([])
        subscribed_user.last_stock_status = False

    return messages

def handle_valid_price(
        subscribed_user: NotificationUser,
        stock_check_result: StockCheckResult,
        in_stock_sizes_for_user_set: Set[str],
        price_str_to_use: str) -> List[str]:
    messages = []

    newly_in_stock_stores_for_user = set(stock_check_result.in_stock_stores).difference(set(subscribed_user.last_in_stock_stores_for_user))
    no_longer_in_stock_stores_for_user = set(subscribed_user.last_in_stock_stores_for_user).difference(set(stock_check_result.in_stock_stores))

    no_longer_in_stock_sizes = set(subscribed_user.last_in_stock_sizes_for_user).difference(in_stock_sizes_for_user_set)
    newly_in_stock_sizes_for_user = in_stock_sizes_for_user_set.difference(set(subscribed_user.last_in_stock_sizes_for_user))

    formatted_in_stock_sizes_for_user = f"In total, tracked size(s), {get_size_requirement_str(in_stock_sizes_for_user_set)}, are in stock."

    if found_new_stock(subscribed_user, newly_in_stock_sizes_for_user, newly_in_stock_stores_for_user):
        newly_in_stock_sizes_str = get_size_requirement_str(newly_in_stock_sizes_for_user)
        available_store_str = "" if not stock_check_result.in_stock_stores else f"at location(s) {', '.join(newly_in_stock_stores_for_user)}"
        if newly_in_stock_sizes_for_user:
            messages.append(f'Size(s) {newly_in_stock_sizes_str} for {subscribed_user.item_name} just went in stock for {price_str_to_use} at ' + \
                            f'{stock_check_result.item_url} {available_store_str}.\n{formatted_in_stock_sizes_for_user}')
        else:
            messages.append(f'Found stock for {stock_check_result.item_name} for {price_str_to_use} at {stock_check_result.item_url} {available_store_str}')
        subscribed_user.last_stock_status = True
    if no_longer_in_stock_sizes:
        if not in_stock_sizes_for_user_set:
            subscribed_user.last_stock_status = False
            messages.append(f'All size(s) being tracked for {stock_check_result.item_name} at {stock_check_result.item_url} are out of stock')
        else:
            no_longer_in_stock_sizes_str = get_size_requirement_str(no_longer_in_stock_sizes)
            size_requirement_msg = f"with sizes {no_longer_in_stock_sizes_str}"
            messages.append(f'Size(s) {size_requirement_msg} just went out of stock for {stock_check_result.item_name} at {stock_check_result.item_url}.\n{formatted_in_stock_sizes_for_user}')
    if no_longer_in_stock_stores_for_user:
        if not stock_check_result.in_stock_stores:
            subscribed_user.last_stock_status = False
            messages.append(f'{stock_check_result.item_name} ({stock_check_result.item_url} just went out of stock for all stores')
        else:
            formatted_in_stock_stores = f"It is still in stock at locations {', '.join(stock_check_result.in_stock_stores)}"
            no_longer_in_stock_stores_str = f"at location(s) {', '.join(no_longer_in_stock_stores_for_user)}"
            messages.append(f'{stock_check_result.item_name} ({stock_check_result.item_url} just went out of stock {no_longer_in_stock_stores_str}.\n{formatted_in_stock_stores}')

    return messages

def check_validity_of_subscribed_sizes(subscribed_user: NotificationUser, stock_check_result: StockCheckResult) -> (bool, str):
    message = ""
    size_requirement_set = set(subscribed_user.stock_options.size_requirement)
    available_sizes_for_user_set = size_requirement_set.intersection(set(stock_check_result.available_sizes))
    unavailable_sizes_for_user_set = size_requirement_set.difference(set(stock_check_result.available_sizes))

    if not available_sizes_for_user_set:
        size_requirement_str = get_size_requirement_str(subscribed_user.stock_options.size_requirement)
        message = f'You have been unsubscribed from {subscribed_user.item_name} at {subscribed_user.item_url} because all of ' + \
        f'the size(s), {size_requirement_str}, you specified are not valid for the item. If the size is more than one word please wrap the size in quotations (ex. "US 0").' + \
        f'Please subscribe again with correct size(s).'
        return False, message
    elif unavailable_sizes_for_user_set:
        unavailable_sizes_str = get_size_requirement_str(unavailable_sizes_for_user_set)
        available_sizes_str = get_size_requirement_str(available_sizes_for_user_set)
        subscribed_user.stock_options.set_size_requirement(available_sizes_for_user_set)
        message = f'Size(s) {unavailable_sizes_str} for item {subscribed_user.item_name} at {subscribed_user.item_url} do not exist. ' + \
        f'You are still subscribed for size(s) {available_sizes_str}'
    return True, message

def found_new_stock(subscribed_user: NotificationUser, newly_in_stock_sizes: Set[str], newly_in_stock_stores_for_user: Set[str]) -> bool:
    return (not subscribed_user.last_stock_status and not subscribed_user.stock_options.size_requirement) or \
           newly_in_stock_sizes or \
           newly_in_stock_stores_for_user

def is_price_over_threshold_for_first_time(subscribed_user: NotificationUser, previous_price_to_use: float) -> bool:
    return verify_price(subscribed_user.stock_options.price_threshold, previous_price_to_use)

def is_stock_check_result_different_for_user(stock_check_result: StockCheckResult, subscribed_user: NotificationUser, in_stock_sizes_for_user_set: Set[str]) -> bool:
    return stock_check_result.is_in_stock != subscribed_user.last_stock_status or \
    in_stock_sizes_for_user_set != subscribed_user.last_in_stock_sizes_for_user or \
    set(stock_check_result.in_stock_stores) != set(subscribed_user.last_in_stock_stores_for_user)

def get_prices_to_use(subscribed_user: NotificationUser, stock_check_result: StockCheckResult, item: Item) -> (float, str, float):
    if subscribed_user.stock_options.official_sites_only:
        price_to_use = stock_check_result.stock_price.min_official_price
        price_str_to_use = stock_check_result.stock_price.min_official_price_str
        previous_price_to_use = math.inf if item.last_stock_check_result == None else item.last_stock_check_result.stock_price.min_official_price
    else:
        price_to_use = stock_check_result.stock_price.min_price
        price_str_to_use = stock_check_result.stock_price.min_price_str
        previous_price_to_use = math.inf if item.last_stock_check_result == None else item.last_stock_check_result.stock_price.min_price

    return price_to_use, price_str_to_use, previous_price_to_use

def verify_price(price_threshold: float, price: float) -> bool:
    return (price_threshold == math.inf and not price == math.inf) or (price != math.inf and price_threshold != math.inf and math.ceil(price) <= math.ceil(price_threshold))

def should_check_size_requirement(size_requirement: List[str], available_sizes: List[str]) -> bool:
    return len(size_requirement) > 0 and available_sizes != NO_IN_STOCK_SIZES
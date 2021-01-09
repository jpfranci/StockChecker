import logging
import math
from typing import List, Tuple, Dict, Optional

import validators
from discord.ext import commands

from conversions.price_history_formatters import format_price_history
from conversions.size_formatters import get_size_requirement_str
from conversions.url_conversions import to_stock_check_url
from model.notification_user import NotificationUser
from model.price_history import PriceHistory
from services import discord_user_service
from services.discord_message_service import DiscordMessageService

class SubscriptionInfoService(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def get_subscribed(self, ctx, num_to_retrieve: Optional[int] = 0):
        all_subscribed: List[NotificationUser] = await discord_user_service.get_all_subscribed_for_user(ctx.message.author.id)
        if all_subscribed:
            price_histories: Dict[str, List[PriceHistory]] = {}
            if num_to_retrieve != 0:
                price_histories = await discord_user_service.get_latest_price_histories(list(map(lambda x: x.item_url, all_subscribed)), num_to_retrieve)
            messages = []
            for notification_user in all_subscribed:
                if notification_user.item_name != "" and notification_user.item_name is not None:
                    item_info_text = f"Item: {notification_user.item_name} ({notification_user.item_url})\n"
                else:
                    item_info_text = f"Item: {notification_user.item_url}\n"

                price_threshold_text = f"Price Threshold: ${notification_user.stock_options.price_threshold:.2f}" if notification_user.stock_options.price_threshold < math.inf else "Price Threshold: any price"
                official_sellers_text = f", including third-party sellers" if not notification_user.stock_options.official_sites_only else ", not including third-party sellers"
                sizes_formatted = get_size_requirement_str(notification_user.stock_options.size_requirement, bolded=False)
                size_text = f"\nTracking sizes: {sizes_formatted}" if sizes_formatted != "" else ""
                item_text = f"{item_info_text}{price_threshold_text}{official_sellers_text}{size_text}\n"
                if num_to_retrieve > 0:
                    price_history_str = format_price_history(notification_user.item_url, price_histories)
                    item_text = f"{item_text}{price_history_str}"
                else:
                    item_text += "\n"

                messages.append(item_text)

            await DiscordMessageService.send_messages(ctx, messages)
        else:
            await ctx.message.channel.send("You are not currently subscribed to anything")

    @commands.command()
    async def get_price_histories(self, ctx, *args):
        if args:
            num_to_retrieve = 5
            effective_args = args
            try:
                num_to_retrieve = int(args[-1])
                effective_args = args[0:-1]
            except Exception as e:
                logging.info(f"{args[-1]} was not an int, will use default number of price histories to fetch")

            valid_urls, invalid_urls = self.partition_urls(list(effective_args))
            price_histories: Dict[str, List[PriceHistory]] = await discord_user_service.get_latest_price_histories(
                valid_urls,
                num_to_retrieve)
            messages = []
            for valid_url in valid_urls:
                item_name = valid_url
                if valid_url in price_histories:
                    item_name = price_histories[item_name][0].stock_check_result.item_name
                messages.append(f"{item_name}\n{format_price_history(valid_url, price_histories)}")

            for invalid_url in invalid_urls:
                messages.append(f"{invalid_url} was not a valid url")

            await DiscordMessageService.send_messages(ctx, messages)
        else:
            await ctx.message.channel.send("There are no items to retrieve price histories for.\n" + \
                                           "Usage !get_price_histories <space separated list of item urls> <last-n-prices> (defaults to 5)")


    # if valid: transforms url to stock check url and adds to valid list
    # if invalid: adds to invalid list
    @staticmethod
    def partition_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
        filtered, filtered_out = [], []
        for url in urls:
            if validators.url(url):
                try:
                    filtered.append(to_stock_check_url(url)[0])
                except Exception as e:
                    filtered_out.append(url)
            else:
                filtered_out.append(url)

        return filtered, filtered_out
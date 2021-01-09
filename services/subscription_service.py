import argparse
import logging
import math
import traceback

import tldextract
import validators
from discord.ext import commands

from conversions.url_conversions import to_stock_check_url
from services import discord_user_service
from conversions.conversions import str2bool, str2size
from conversions.size_formatters import get_size_requirement_str
from model.notification_user import NotificationUser
from model.stock_options import StockOptions
from model.user_exception import UserException
from settings.messages import subscribe_help_message

class SubscriptionService(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def subscribe(self, ctx, *args):
        parser = argparse.ArgumentParser(description='Subscribe to a website and be notified when a price dips below a threshold')
        parser.add_argument('url', type=str, help='The url for the item that you want to monitor.')
        parser.add_argument('-t', '--threshold', type=float, default=math.inf, help="Specify the price threshold to be notified. Defaults to any price.")
        parser.add_argument('-o', '--official-only', type=str2bool, default=True, help="Only be notified when official sources go in stock (for example Amazon). Defaults to True")
        parser.add_argument('-s', '--sizes', default=[], type=str2size, nargs='+', help="For clothes in clothing sites, the clothing size that is being sought after.")

        response: str = ""

        try:
            parsed_args = parser.parse_args(args)
            url = parsed_args.url.strip()
            stock_options = StockOptions(
                parsed_args.threshold,
                parsed_args.official_only,
                parsed_args.sizes)

            if validators.url(url):
                try:
                    stock_check_url, website = to_stock_check_url(url)
                    notification_user = self.to_notification_user(ctx, stock_options, stock_check_url)
                    item = await discord_user_service.subscribe(notification_user, stock_check_url, website)

                    item_name_to_use = item.item_name if item.item_name != "" and item.item_name is not None else url
                    price_text = f"goes below or equal to ${stock_options.price_threshold:.2f}" if stock_options.price_threshold < math.inf else "is in stock"
                    source = f'and sold by {website.value} directly' if stock_options.official_sites_only else f"and sold by any seller on {website.value}"
                    size_joined_str = get_size_requirement_str(stock_options.size_requirement)
                    size = f" with size(s) {size_joined_str}" if stock_options.size_requirement else ""
                    response = f"Successfully subscribed to be notified when **{item_name_to_use}** {price_text}{size} {source}"
                except UserException as ue:
                    response = str(ue)
                except Exception as e:
                    logging.error(traceback.format_exc())
                    logging.error(e)
                    response = f"The website {tldextract.extract(url).domain} is not supported at this time"
        except SystemExit:
            await ctx.message.channel.send(subscribe_help_message)

        if response != "":
            await ctx.message.channel.send(response)

    @commands.command()
    async def unsubscribe(self, ctx, arg):
        url = arg.strip()
        response = "You are not subscribed to the item."
        try:
            stock_check_url: str = to_stock_check_url(url)[0]
            notification_user = self.to_notification_user(ctx, StockOptions.create_default(), stock_check_url)
            await discord_user_service.unsubscribe(stock_check_url, notification_user)
            response = f"Successfully unsubscribed from {url}"
        except UserException as ue:
            response = str(ue)
        except Exception as e:
            response = "The item was not valid."
            logging.error(traceback.format_exc())
            logging.error(e)

        await ctx.message.channel.send(response)

    @commands.command()
    async def unsubscribe_all(self, ctx):
        try:
            await discord_user_service.unsubscribe_all(ctx.message.author.id)
            await ctx.message.channel.send("Successfully unsubscribed from all items tracked")
        except UserException as ue:
            await ctx.message.channel.send(str(ue))

    @staticmethod
    def to_notification_user(ctx, stock_options, item_url) -> NotificationUser:
        return NotificationUser(
            ctx.message.author.id,
            stock_options,
            False,
            item_url)
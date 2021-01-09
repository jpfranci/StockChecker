import asyncio
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List

import discord
from discord.ext import commands

import stock_check_result_reporter
from conversions.message_formatters import chunk_messages
from model import website
from services.chrono_service import ChronoService
from services.stock_check_loops import StockCheckLoops
from settings.messages import current_commands

class DiscordMessageService(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        executor = ThreadPoolExecutor(max_workers=3)
        stock_check_loops = StockCheckLoops(self.bot)
        logging.info(f'{self.bot.user} has connected to Discord!')
        loop = asyncio.get_event_loop()
        executor.submit(ChronoService().execute)
        if website.requests_website_dict:
            executor.submit(stock_check_loops.run_request_stock_loop, loop)
        if website.selenium_website_dict:
            executor.submit(stock_check_loops.run_selenium_stock_loop, loop)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome = f"Welcome {member.name}, please DM me if you want to track the stock status of an item! For help on commands, message me !help through a DM."
        await stock_check_result_reporter.send_message(member.id, welcome)
        await stock_check_result_reporter.send_message(member.id, current_commands)

    @staticmethod
    async def send_messages(ctx, messages: List[str]) -> None:
        message_chunks = chunk_messages(messages)
        tasks = [ctx.message.channel.send(chunk) for chunk in message_chunks]
        await asyncio.gather(*tasks)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.CommandNotFound):
            await ctx.message.channel.send(current_commands)
        else:
            logging.error(error)
from services.discord_message_service import DiscordMessageService
from services.subscription_info_service import SubscriptionInfoService
from services.subscription_service import SubscriptionService
from discord.ext import commands

from services.tasks.log_file_task import LogFileTask
from settings.settings import DISCORD_TOKEN

LogFileTask.create_new_logger()

def main():
    bot = commands.Bot(command_prefix='!')
    bot.remove_command("help")
    bot.add_cog(DiscordMessageService(bot))
    bot.add_cog(SubscriptionService(bot))
    bot.add_cog(SubscriptionInfoService(bot))
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
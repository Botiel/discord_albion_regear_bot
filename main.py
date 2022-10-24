from regearbot_package.config import DISCORD_TOKEN
from regearbot_package.events import Commands
from discord.message import Message
import discord
import logging
import os
from datetime import datetime as dt


intents = discord.Intents().all()
client = discord.Client(intents=intents)


def handle_logs():
    now = dt.now().strftime("%Y-%m-%d")
    folder = f'./discord_logs'
    log_path = f'./discord_logs/log_{now}.logs'

    if not os.path.exists(folder):
        os.makedirs(folder)

    return logging.FileHandler(filename=log_path, encoding='utf-8', mode='w')


@client.event
async def on_ready():
    print(f'Process ID: {os.getpid()}')
    print(f'Session Id: {client.ws.session_id}')
    print(f'Thread Id: {client.ws.thread_id}')
    print("Bot is up!")


@client.event
async def on_message(msg: Message):
    if msg.author == client.user:
        return

    commands = Commands(msg=msg, client=client)

    if commands.check_if_command() == 'no':
        await msg.channel.send("Invalid Command, use !help_me")
        return

    elif commands.check_if_command() == 'msg':
        return

    elif commands.check_if_command() == 'yes':
        await commands.help_command()
        await commands.player_mmr_command()
        await commands.all_recent_deaths_command()
        await commands.last_death_command()
        await commands.submit_regear_request_command()
        await commands.get_all_regear_requests_from_db_command()
        await commands.get_regear_quantity_from_db_command()
        await commands.get_builds_sheet_template_command()
        await commands.upload_zvz_builds_command()
        await commands.clear_zvz_builds_collection_command()
        await commands.deny_event_id_command()
        await commands.remove_regear_request_command()


if __name__ == '__main__':
    # run without writing logs to a file
    client.run(DISCORD_TOKEN)

    # run with logs file output
    # client.run(DISCORD_TOKEN, log_handler=handle_logs(), log_level=logging.DEBUG)





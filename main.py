from regearbot_package.config import DISCORD_TOKEN
from regearbot_package.events import Commands, Encourage
from discord.message import Message
import discord

intents = discord.Intents().all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("Bot is up!")


@client.event
async def on_message(msg: Message):

    if msg.author == client.user:
        return

    encouragement = Encourage(msg=msg, client=client)
    await encouragement.check_if_needs_encouragement()

    commands = Commands(msg=msg, client=client)
    if not commands.check_if_command():
        await msg.channel.send("Invalid Command, use !help")
        return
    else:
        await commands.help_command()
        await commands.player_mmr_command()
        await commands.all_recent_deaths_command()
        await commands.last_death_command()
        await commands.submit_regear_request_command()

if __name__ == '__main__':
    client.run(DISCORD_TOKEN)

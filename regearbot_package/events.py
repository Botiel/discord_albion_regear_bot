from discord.client import Client
from discord.message import Message
from regearbot_package.api_calls import AlbionApi, ReGearCalls
from random import choice
from discord import Embed


class Commands:
    images_channel = 1024344203100168312

    def __init__(self, msg: Message, client: Client):
        self.msg = msg
        self.client = client
        self.content = self.msg.content.split(" ")

    async def create_regear_embed_objects(self, display_list: list, is_last=False):

        for i, item in enumerate(display_list):
            desc = f"EventId: {item['EventId']}\n" \
                   f"Date: {item['TimeStamp'].split('T')[0]}\n" \
                   f"Time: {item['TimeStamp'].split('T')[1]}\n" \
                   f"AverageItemPower: {item['AverageItemPower']}\n"

            file = AlbionApi.convert_images_to_a_single_image(image_list=item["items_as_png"])
            images_channel = self.client.get_channel(self.images_channel)
            msg_id = await images_channel.send(file=file)
            info_embed = Embed(title=f"{self.content[1]} Last Death:", description=desc)
            info_embed.set_image(url=msg_id.attachments[0].url)
            await self.msg.author.send(embed=info_embed)

            if is_last:
                return

    def check_if_command(self):
        first_char = self.content[0][0]  # Checks for "!" sign
        first_word = self.content[0][1:]  # Checks the command
        commands_quantity = len(self.content)  # Checks quantity of args

        if first_char == '!':
            if first_word == 'help' and commands_quantity == 1:
                return True
            elif first_word != 'help' and first_word != 'regear' and commands_quantity == 2:
                return True
            elif first_word == 'regear' and commands_quantity == 3:
                return True
            else:
                return False

        return True

    async def help_command(self):
        if self.content[0] == "!help":
            await self.msg.author.send("Greetings Noob!\n"
                                       "Command List:\n"
                                       "    !player_mmr <Player Name>\n"
                                       "    !deaths <Player Name>\n"
                                       "    !last_death <Player Name>\n"
                                       "    !regear <Player Name> <EventId>\n")

    async def player_mmr_command(self):
        if self.content[0] == "!player_mmr":
            mmr = AlbionApi.get_player_mmr(name=self.content[1])[-1]
            msg = f'{self.content[1]} Recent Mmr: {mmr}'
            await self.msg.channel.send(msg)

    async def all_recent_deaths_command(self):
        if self.content[0] == "!deaths":
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            api.get_display_format()
            await self.create_regear_embed_objects(display_list=api.display_list)

    async def last_death_command(self):
        if self.content[0] == "!last_death":
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            api.get_display_format()
            await self.create_regear_embed_objects(display_list=api.display_list, is_last=True)

    async def submit_regear_request_command(self):
        if self.content[0] == "!regear":
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            if api.submit_regear_request(event_id=self.content[2]):
                await self.msg.channel.send(f"EventId[{self.content[2]}] submitted successfully")
            else:
                await self.msg.channel.send(f"EventId[{self.content[2]}] has already been submitted or not exist!")


class Encourage:
    sad_words = ['sad', 'noob', 'angry', 'unhappy', 'depressed']
    encouragements = [
        "Cheer up! grind more!",
        "Dont be sad, Yocttar is much noober than you :)",
        "You are great! at least you are not fat like yocttar! :D",
        "Don't worry! one day you will be good at this game!"
    ]

    def __init__(self, msg: Message, client: Client):
        self.msg = msg
        self.client = client
        self.content = self.msg.content

    async def check_if_needs_encouragement(self):
        if any(word in self.content for word in self.sad_words):
            await self.msg.channel.send(choice(self.encouragements))

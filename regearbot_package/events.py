from discord.client import Client
from discord.message import Message
from discord import Embed
from regearbot_package.config import CHANNELS_ID
from regearbot_package.api_calls import AlbionApi, ReGearCalls, MongoDataManager
from random import choice


class Commands:
    images_channel = CHANNELS_ID.get("regear-images")
    admins_channel = CHANNELS_ID.get("regear-admins")
    users_channel = CHANNELS_ID.get("regear-users")

    def __init__(self, msg: Message, client: Client):
        self.msg = msg
        self.client = client
        self.content = self.msg.content.split(" ")

    async def create_regear_embed_objects(self, display_list: list, is_last=False):

        embed_list = []

        for i, item in enumerate(display_list):

            # Creating an Embed description variable
            date = item['TimeStamp'].split('T')[0]
            time = item['TimeStamp'].split('T')[1].split('.')[0]
            desc = f"EventId: {item['EventId']}\n" \
                   f"Date: {date}\n" \
                   f"Time: {time}\n" \
                   f"AverageItemPower: {item['AverageItemPower']}\n" \
                   f"Url: https://albiononline.com/en/killboard/kill/{item['EventId']}\n"

            # Concatenating all item images to a single image
            file = AlbionApi.convert_images_to_a_single_image(image_list=item["items_as_png"])

            # Getting images channel id for uploading images
            images_channel = self.client.get_channel(self.images_channel)
            msg_id = await images_channel.send(file=file)

            # Creating an Embed object
            info_embed = Embed(title=f"{self.content[1]} Last Death:", description=desc)
            info_embed.set_image(url=msg_id.attachments[0].url)

            # If querying only for last death then return last death embed else append embed to list
            if is_last:
                await self.msg.author.send(embed=info_embed)
                return
            else:
                embed_list.append(info_embed)

        # Send to author all death embed objects
        await self.msg.author.send(embeds=embed_list)

    def check_if_command(self):
        if self.content:
            first_char = self.content[0][0]  # Checks for "!" sign
            first_word = self.content[0][1:]  # Checks the command
            commands_quantity = len(self.content)  # Checks quantity of args
        else:
            return 'msg'

        if first_char == '!':
            if first_word == 'help' and commands_quantity == 1:
                return 'yes'
            elif first_word == 'pull_regear_requests' and commands_quantity == 1:
                return 'yes'
            elif first_word != 'help' and first_word != 'regear' and commands_quantity == 2:
                return 'yes'
            elif first_word == 'regear' and commands_quantity == 3:
                return 'yes'
            else:
                return 'no'

        return 'msg'

    async def help_command(self):
        if self.content[0] == "!help":
            await self.msg.author.send("Greetings Noob!\n\n"
                                       "Users command List:\n"
                                       "    !player_mmr <Player Name>\n"
                                       "    !deaths <Player Name>\n"
                                       "    !last_death <Player Name>\n"
                                       "    !regear <Player Name> <EventId>\n\n"
                                       "Admins Only:\n"
                                       "    !pull_regear_requests\n"
                                       "    !regear_quantity <true/false>")

    async def player_mmr_command(self):
        if self.content[0] == "!player_mmr" and self.msg.channel.id == self.users_channel:
            mmr = AlbionApi.get_player_mmr(name=self.content[1])[-1]
            msg = f'{self.content[1]} Recent Mmr: {mmr}'
            await self.msg.channel.send(msg)

    async def all_recent_deaths_command(self):
        if self.content[0] == "!deaths" and self.msg.channel.id == self.users_channel:
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            api.get_display_format()
            await self.msg.author.send('Processing information [approximately 10 seconds]...')
            await self.create_regear_embed_objects(display_list=api.display_list)

    async def last_death_command(self):
        if self.content[0] == "!last_death" and self.msg.channel.id == self.users_channel:
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            api.get_display_format()
            await self.create_regear_embed_objects(display_list=api.display_list, is_last=True)

    async def submit_regear_request_command(self):
        if self.content[0] == "!regear" and self.msg.channel.id == self.users_channel:
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            if api.submit_regear_request(event_id=self.content[2]):
                await self.msg.channel.send(f"EventId[{self.content[2]}] submitted successfully")
            else:
                await self.msg.channel.send(f"EventId[{self.content[2]}] has already been submitted or not exist!")

    async def get_all_regear_requests_from_db_command(self):
        if self.content[0] == "!pull_regear_requests" and self.msg.channel.id == self.admins_channel:
            await self.msg.channel.send('Processing information...')
            file = ReGearCalls.convert_regear_objects_to_csv()
            await self.msg.channel.send(file=file)

    async def get_regear_quantity_from_db_command(self):
        if self.content[0] == "!regear_quantity" and self.msg.channel.id == self.admins_channel:
            mongo = MongoDataManager()
            match self.content[1]:
                case 'false':
                    quantity = mongo.get_quantity_of_objects_by_regear(is_regeared=False)
                    await self.msg.channel.send(f'Pending for regear: {quantity} players')
                case 'true':
                    quantity = mongo.get_quantity_of_objects_by_regear(is_regeared=True)
                    await self.msg.channel.send(f'Regeared Players: {quantity}')
                case _:
                    await self.msg.channel.send('Invalid command, second argument must be true or false!')
                    return


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

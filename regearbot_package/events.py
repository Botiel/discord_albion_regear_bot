from discord.client import Client
from discord.message import Message
from discord import Embed
from regearbot_package.config import CHANNELS_ID
from regearbot_package.api_calls import AlbionApi, ReGearCalls, MongoDataManager, MongoZvzBuildsManager
from regearbot_package.object_classes import ZvzApprovedBuild
from random import choice


class Commands:
    images_channel = CHANNELS_ID.get("regear_images")
    admins_channel = CHANNELS_ID.get("regear_admins")
    users_channel = CHANNELS_ID.get("regear_users")

    def __init__(self, msg: Message, client: Client):
        self.msg = msg
        self.client = client
        self.content = self.msg.content.split(" ")

    async def create_zvz_build_embed_objects(self, build_list: list):

        embed_list = []

        # Creating an Embed description variable
        for i, build in enumerate(build_list):
            date = build['time_stamp'].split(' ')[0]
            time = build['time_stamp'].split(' ')[1]
            desc = f'**Date:** {date}\n' \
                   f'**Time:** {time}\n\n' \
                   f'**Main Hand:** {build["main_hand"]}\n' \
                   f'**Off Hand:** {build["off_hand"]}\n' \
                   f'**Helmet:** {build["helmet"]}\n' \
                   f'**Chest:** {build["chest"]}\n' \
                   f'**Boots:** {build["boots"]}\n' \
                   f'**Item Power:** {build["item_power"]}\n'

            # Concatenating all item images to a single image
            file = AlbionApi.convert_images_to_a_single_image(image_list=build["items_as_png"])

            # Getting images channel id for uploading images
            images_channel = self.client.get_channel(self.images_channel)
            msg_id = await images_channel.send(file=file)

            embed = Embed(title=f'Zvz Build: {build.get("role")}', description=desc)
            embed.set_image(url=msg_id.attachments[0].url)
            embed_list.append(embed)

        # Send to author all death embed objects
        await self.msg.channel.send(embeds=embed_list)

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

        first_char = self.content[0][0]  # Checks for "!" sign
        first_word = self.content[0][1:]  # Checks the command
        commands_quantity = len(self.content)  # Checks quantity of args

        command_rules = [first_word == 'help_me' and commands_quantity == 1,
                         first_word == 'pending' and commands_quantity == 1,
                         first_word == 'pull_regear_requests' and commands_quantity == 1,
                         first_word == "deaths" and commands_quantity == 2,
                         first_word == "player_mmr" and commands_quantity == 2,
                         first_word == "last_death" and commands_quantity == 2,
                         first_word == 'regear' and commands_quantity == 3,
                         first_word == 'zvz_build_instructions' and commands_quantity == 1,
                         first_word == 'show_builds' and commands_quantity == 2,
                         first_word == 'add_setup']

        if first_char == '!':
            if any(command_rules):
                return 'yes'
            else:
                return 'no'

        return 'msg'

    async def help_command(self):
        if self.content[0] == "!help_me":

            # Descriptions for the commands
            users_desc = "!player_mmr <Player Name>\n\n" \
                         "!deaths <Player Name>\n\n" \
                         "!last_death <Player Name>\n\n" \
                         "!regear <Player Name> <EventId>"

            admins_desc = "!pull_regear_requests\n\n" \
                          "!pending\n\n" \
                          "!zvz_build_instructions"

            # !help_me embed item by channel
            users_embed = Embed(title='User Commands:', description=users_desc)
            admins_embed = Embed(title='Admin Commands:', description=admins_desc)

            # send !help_me embed by channel id
            if self.msg.channel.id == self.users_channel:
                await self.msg.author.send(embed=users_embed)
            elif self.msg.channel.id == self.admins_channel:
                await self.msg.author.send(embed=admins_embed)

    async def player_mmr_command(self):
        if self.content[0] == "!player_mmr" and self.msg.channel.id == self.users_channel:

            try:
                mmr = AlbionApi.get_player_mmr(name=self.content[1])[-1]
            except IndexError:
                await self.msg.channel.send('No such player...')
            else:
                desc = f'Player Name: {self.content[1]}\n' \
                       f'Time: {mmr.get("time")}\n' \
                       f'Rating: {mmr.get("value")}'
                mmr_embed = Embed(title='Recent MMR:', description=desc)
                await self.msg.channel.send(embed=mmr_embed)

    async def all_recent_deaths_command(self):
        if self.content[0] == "!deaths" and self.msg.channel.id == self.users_channel:
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            api.get_display_format()

            try:
                await self.create_regear_embed_objects(display_list=api.display_list)
            except Exception as e:
                print(e)
                await self.msg.channel.send('No such player...')
            else:
                await self.msg.author.send('Processing information [approximately 10 seconds]...')

    async def last_death_command(self):
        if self.content[0] == "!last_death" and self.msg.channel.id == self.users_channel:
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            api.get_display_format()
            try:
                await self.create_regear_embed_objects(display_list=api.display_list, is_last=True)
            except Exception as e:
                print(e)
                await self.msg.channel.send('No such player...')

    async def submit_regear_request_command(self):
        if self.content[0] == "!regear" and self.msg.channel.id == self.users_channel:
            api = ReGearCalls(name=self.content[1])
            api.get_deaths_info()
            if api.submit_regear_request(event_id=self.content[2]):
                desc = f'Event Id: {self.content[2]}\nStatus: submitted successfully'
                embed = Embed(title='Regear Request:', description=desc)
                await self.msg.channel.send(embed=embed)
            else:
                desc = f'Event Id: {self.content[2]}\nStatus: has already been submitted or not exist!'
                embed = Embed(title='Regear Request:', description=desc)
                await self.msg.channel.send(embed=embed)

    async def get_all_regear_requests_from_db_command(self):
        if self.content[0] == "!pull_regear_requests" and self.msg.channel.id == self.admins_channel:
            await self.msg.channel.send('Processing information...')
            file = ReGearCalls.convert_regear_objects_to_csv()
            await self.msg.channel.send(file=file)

    async def get_regear_quantity_from_db_command(self):
        if self.content[0] == "!pending" and self.msg.channel.id == self.admins_channel:
            mongo = MongoDataManager()
            quantity_false = mongo.get_quantity_of_objects_by_regear(is_regeared=False)
            quantity_true = mongo.get_quantity_of_objects_by_regear(is_regeared=True)
            desc = f'Pending for regear: {quantity_false}\n' \
                   f'Regeared Players: {quantity_true}'
            embed = Embed(title='Regearing Status:', description=desc)
            await self.msg.channel.send(embed=embed)

    async def create_zvz_build_object_command(self):
        if self.content[0] == "!add_setup" and self.msg.channel.id == self.admins_channel:

            # STEP[1]: create and validate build
            build = ZvzApprovedBuild()
            validate = build.validate_build_request(msg_content=self.msg.content)
            if not validate.get('status'):
                embed = Embed(title='Setup Error:',
                              description=f'error type: {validate.get("message")}\n\nCheck Instructions!')
                await self.msg.channel.send(embed=embed)
                return

            # STEP[2]: upload build to mongodb
            mongo = MongoZvzBuildsManager()
            result = mongo.upload_zvz_build(build=build.dict())
            if result.get('status'):
                await self.msg.channel.send(result.get('message'))
            else:
                await self.msg.channel.send(f"Something went wrong!\nError: {result.get('message')}")

    async def zvz_build_instructions_command(self):
        if self.content[0] == "!zvz_build_instructions" and self.msg.channel.id == self.admins_channel:
            desc = "How to add zvz approved build:\n\n" \
                   "Example:\n!add_setup [role,main_hand,off_hand,helmet,chest,boots,item_power]\n\n" \
                   "1. start with !add_setup command followed by a space bar\n" \
                   "2. build must me enclosed by brackets []\n" \
                   "3. insert values in the same order as in the example\n" \
                   "4. if there is no off_hand item, insert: any\n" \
                   "5. number of values inside the brackets must be 7\n" \
                   "6. all values must be comma separated with no spaces (csv style)\n" \
                   "7. roles: dps, healer, tank, support"
            embed = Embed(title='Zvz build instructions', description=desc)
            await self.msg.author.send(embed=embed)

    async def show_zvz_available_builds(self):
        if self.content[0] == "!show_builds" and self.msg.channel.id == self.admins_channel:
            mongo = MongoZvzBuildsManager()
            response = mongo.request_all_zvz_build_objects(query=self.content[1])

            if not response.get('status'):
                await self.msg.channel.send(f"Something went wrong!\nError: {response.get('message')}")

            if not response.get('content'):
                await self.msg.channel.send('No Builds in the DataBase...')
            else:
                await self.msg.channel.send('Processing Information...')
                await self.create_zvz_build_embed_objects(build_list=response.get('content'))


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

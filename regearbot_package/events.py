from discord.client import Client
from discord.message import Message
from discord import Embed
from regearbot_package.config import CHANNELS_ID
from regearbot_package.mongo_database import MongoDataManager, MongoZvzBuildsManager
from regearbot_package.bot_api import ReGearCalls, AlbionApi, DataConversion


class Commands:
    images_channel = CHANNELS_ID.get("regear_images")
    admins_channel = CHANNELS_ID.get("regear_admins")
    users_channel = CHANNELS_ID.get("regear_users")

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

        first_char = self.content[0][0]  # Checks for "!" sign
        first_word = self.content[0][1:]  # Checks the command
        commands_quantity = len(self.content)  # Checks quantity of args

        command_rules = [first_word == 'help_me' and commands_quantity == 1,
                         first_word == 'pending' and commands_quantity == 1,
                         first_word == 'pull_regear_requests' and commands_quantity == 1,
                         first_word == "deaths" and commands_quantity == 2,
                         first_word == "player_mmr" and commands_quantity == 2,
                         first_word == "last_death" and commands_quantity == 2,
                         first_word == 'remove_request' and commands_quantity == 2,
                         first_word == 'deny' and commands_quantity == 2,
                         first_word == 'regear' and commands_quantity == 2,
                         first_word == 'get_builds_sheet_template' and commands_quantity == 1,
                         first_word == 'upload_zvz_builds' and commands_quantity == 1,
                         first_word == 'clear_zvz_builds' and commands_quantity == 1,
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
                         "!regear <EventId>"

            admins_desc = "!pull_regear_requests\n\n" \
                          "!pending\n\n" \
                          "!get_builds_sheet_template\n\n" \
                          "!upload_zvz_builds\n\n" \
                          "!clear_zvz_builds\n\n" \
                          "!remove_request <EventId>\n\n" \
                          "!deny <EventId>"

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

            await self.msg.author.send('Processing information [approximately 20 seconds]...\nPulling last 10 deaths!')

            try:
                await self.create_regear_embed_objects(display_list=api.display_list)
            except Exception as e:
                print(e)
                await self.msg.channel.send('No such player...')

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
            response = ReGearCalls.submit_regear_request(event_id=self.content[1])
            embed = Embed(title='Regear Request status:')

            if response.get("status"):
                desc = f'**Event Id:** {self.content[1]}\n**response:** submitted successfully'
                embed.description = desc
            else:
                desc = f'**Event Id:** {self.content[1]}\n**response:** request denied!\n' \
                       f'**message**: {response.get("message")}'
                embed.description = desc

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

    async def get_builds_sheet_template_command(self):
        if self.content[0] == "!get_builds_sheet_template" and self.msg.channel.id == self.admins_channel:
            await self.msg.channel.send(file=DataConversion.get_builds_sheet())

    async def upload_zvz_builds_command(self):
        if self.content[0] == "!upload_zvz_builds" and self.msg.channel.id == self.admins_channel:
            try:
                attachment = self.msg.attachments[0]
            except Exception as e:
                embed = Embed(title="Upload Error",
                              description=f"**message:** No files attached to the command...\n**Error:** {e}")
                await self.msg.channel.send(embed=embed)
                return

            await attachment.save("./regearbot_package/data/zvz_builds_to_upload.xlsx")
            try:
                builds = DataConversion.convert_zvz_builds_sheet_to_dict()
            except Exception as e:
                embed = Embed(title="Upload Error", description=f"**Error:** {e}")
                await self.msg.channel.send(embed=embed)
            else:
                mongo = MongoZvzBuildsManager()
                response = mongo.upload_zvz_builds(builds=builds)

                embed = Embed(title="Upload Status")
                if response.get("status"):
                    embed.description = f"**message:** {response.get('message')}"
                else:
                    embed.description = f"**message:** {response.get('message')}\n**error**: {response.get('error')}"

                await self.msg.channel.send(embed=embed)

    async def clear_zvz_builds_collection_command(self):
        if self.content[0] == "!clear_zvz_builds" and self.msg.channel.id == self.admins_channel:
            mongo = MongoZvzBuildsManager()
            response = mongo.clear_zvz_builds()
            embed = Embed(title="Zvz Builds Collection Status:")

            if response.get("status"):
                embed.description = f"**message:** {response.get('message')}\n**deleted builds:** {response.get('count')}"
            else:
                embed.description = f"**message:** {response.get('message')}\n**error:** {response.get('error')}"

            await self.msg.channel.send(embed=embed)

    async def remove_regear_request_command(self):
        if self.content[0] == "!remove_request" and self.msg.channel.id == self.admins_channel:
            embed = Embed(title="Remove request status:")

            try:
                event_id = int(self.content[1])
            except ValueError:
                embed.description = "**error**: EventId must be a number"
                await self.msg.channel.send(embed=embed)
                return

            mongo = MongoDataManager()

            try:
                response = mongo.remove_object_by_event_id(event_id=event_id)
            except Exception as e:
                embed.description = f"**error**: {e}"
                await self.msg.channel.send(embed=embed)
                return

            if response:
                embed.description = f"**message**: removed event {event_id} successfully"
            else:
                embed.description = f"**message**: no such event {event_id} in the database"
            await self.msg.channel.send(embed=embed)

    async def deny_event_id_command(self):
        if self.content[0] == "!deny" and self.msg.channel.id == self.admins_channel:
            embed = Embed(title="Deny request status:")

            try:
                event_id = int(self.content[1])
            except ValueError:
                embed.description = "**error**: EventId must be a number"
                await self.msg.channel.send(embed=embed)
                return

            mongo = MongoDataManager()

            try:
                mongo.add_denied_event_id(event_id=event_id)
            except Exception as e:
                embed.description = f"**error**: {e}"
            else:
                embed.description = f"**message**: event {event_id} is denied"

            await self.msg.channel.send(embed=embed)







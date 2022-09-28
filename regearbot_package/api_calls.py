import requests
from pprint import pprint
from regearbot_package.object_classes import Death
from regearbot_package.mogodb_data_manager import MongoDataManager
from PIL import Image
import io
import discord


class AlbionApi:
    albion_url = "https://gameinfo.albiononline.com/api/gameinfo"
    murder_url = "https://murderledger.com/api"
    render_item = "https://render.albiononline.com/v1/item"

    @classmethod
    def get_player_id(cls, name: str) -> str:
        url = f'{cls.albion_url}/search?q={name}'
        return requests.get(url=url).json()["players"][0].get("Id")

    @classmethod
    def get_player_info(cls, player_id: str) -> dict:
        url = f"{cls.albion_url}/players/{player_id}"
        return requests.get(url=url).json()

    @classmethod
    def request_death_info(cls, player_id: str) -> dict:
        # Will return the last 10 kills info
        url = f'{cls.albion_url}/players/{player_id}/deaths'
        return requests.get(url=url).json()

    @classmethod
    def get_player_mmr(cls, name: str) -> list:
        url = f"{cls.murder_url}/players/{name}/elo-chart"
        return requests.get(url=url).json()["data"]

    @classmethod
    def request_render_item(cls, item: str) -> str:
        return f"{cls.render_item}/{item}.png"

    @classmethod
    def convert_images_to_a_single_image(cls, image_list: list) -> discord.File:

        # Requesting images from api
        pillow_imgs = []
        for img in image_list:
            response = requests.get(url=img, stream=True).raw
            pillow_imgs.append(Image.open(response))

        # Concatenating images to a single image
        new_img = Image.new(mode='RGB', size=(1450, 230), color=(192, 192, 192))
        x = 20
        for item in pillow_imgs:
            new_img.paste(item, (x, 0))
            x += 200

        # Converting black spaces into grey
        data = new_img.getdata()
        temp_img = []
        for item in data:
            if item == (0, 0, 0):
                temp_img.append((192, 192, 192))
            else:
                temp_img.append(item)

        # injecting new data to new_img
        new_img.putdata(temp_img)

        arr = io.BytesIO()
        new_img.save(arr, format='PNG')
        arr.seek(0)
        return discord.File(fp=arr, filename="items.png")


class ReGearCalls:

    def __init__(self, name: str):
        self.player_id = AlbionApi.get_player_id(name=name)
        self.deaths_list = AlbionApi.request_death_info(player_id=self.player_id)
        self.victim_info_list = []  # list of objects for MongoDB
        self.display_list = []  # list of objects to display on Discord

    def get_deaths_info(self):  # convert deaths list items from albion api object to ReGearInfo object
        for death in self.deaths_list:
            info = Death(**death)
            self.victim_info_list.append(info.convert_to_dict())

    def get_display_format(self):

        for victim in self.victim_info_list:
            temp = {
                "EventId": victim.get("EventId"),
                "TimeStamp": victim.get("TimeStamp"),
                "AverageItemPower": victim['Victim'].get("AverageItemPower"),
                "items_as_png": []
            }

            # convert items to png
            equipment = victim['Victim'].get("Equipment")
            inventory = victim['Victim'].get("Inventory")

            if equipment:
                for item in equipment:
                    for k, v in item.items():
                        temp["items_as_png"].append(AlbionApi.request_render_item(item=v))

            if inventory:
                for item in inventory:
                    temp["items_as_png"].append(AlbionApi.request_render_item(item=item))

            self.display_list.append(temp)

    def submit_regear_request(self, event_id: str):
        mongo_client = MongoDataManager()
        for item in self.victim_info_list:
            if int(event_id) == item.get('EventId'):
                return mongo_client.upload_objects_to_db(victim_object=item)

    def print_victim_death_list(self):
        pprint(self.victim_info_list)

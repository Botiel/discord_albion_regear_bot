import requests
from pprint import pprint
from regearbot_package.object_classes import Death
from PIL import Image
from pymongo import MongoClient
from regearbot_package.config import MONGO_CLIENT
import pandas as pd
import io
import discord
import json


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

    @classmethod
    def convert_regear_objects_to_csv(cls):

        # STEP[1] Importing objects from mongodb
        mongo = MongoDataManager()
        docs = mongo.request_objects_to_regear(convert_to_regear=True)

        # STEP[2] importing items dict
        with open('./regearbot_package/data/items_dict.json', 'r') as f:
            data = json.load(f)

        # STEP[3] creating dataframe for csv
        temp = {'Name': [],
                'EventId': [],
                'AverageItemPower': [],
                'Items': []
                }
        for doc in docs:
            temp['Name'].append(doc['Victim'].get('Name'))
            temp['EventId'].append(f"https://albiononline.com/en/killboard/kill/{doc.get('EventId')}")
            temp['AverageItemPower'].append(doc['Victim'].get('AverageItemPower'))

            items = []
            equipment = doc['Victim'].get('Equipment')
            inventory = doc['Victim'].get('Inventory')
            for item in equipment:
                for k, v in item.items():
                    items.append(data[v])

            if inventory:
                for item in inventory:
                    items.append(data[item])

            temp['Items'].append(items)
        df = pd.DataFrame(temp)

        # STEP[4] save as binary (discord file)
        arr = io.BytesIO()
        df.to_csv(arr, index=False, sep=",")
        arr.seek(0)
        return discord.File(fp=arr, filename="regear_requests.csv")

    def print_victim_death_list(self):
        pprint(self.victim_info_list)


class MongoDataManager:
    def __init__(self, database="albion", database_collection="regearbot"):
        self.client = MongoClient(MONGO_CLIENT)
        self.db = self.client.get_database(database)
        self.collection = self.db.get_collection(database_collection)

    def upload_objects_to_db(self, victim_object: dict) -> bool:
        # checks EventId, if no object with the same EventId -> Upload
        event_id = victim_object.get('EventId')
        query = self.collection.find_one({"EventId": event_id})

        if query:
            return False
        else:
            self.collection.insert_one(victim_object)
            return True

    def request_objects_to_regear(self, convert_to_regear=False) -> list:

        # STEP[1] get all objects where is_regeared = False
        query = {"is_regeared": False}
        cursor = self.collection.find(query)
        docs = list(cursor).copy()

        # STEP[2] convert all exported objects to is_regeared = True
        if convert_to_regear:
            new_values = {"$set": {"is_regeared": True}}
            self.collection.update_many(query, new_values)

        return docs

    # ----------------- MANAGEMENT DEBUG METHODS -------------------

    def delete_objects_from_db(self):
        my_query = {"category": ""}
        query = self.collection.delete_one(my_query)
        print(query.deleted_count)

    def delete_multiple_objects_from_db(self):
        my_query = {"category": "Victim_to_regear"}
        query = self.collection.delete_many(my_query)
        print(query.deleted_count, " jsons deleted.")

    def get_quantity_of_objects_in_collection(self):
        query = self.collection.count_documents({"category": "Victim_to_regear"})
        print(query)

    def search_object_by_event_id(self, event_id: int) -> bool:
        query = self.collection.find_one({"EventId": event_id})
        return True if query else False

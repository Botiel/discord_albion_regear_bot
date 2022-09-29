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
import os
import sys


CURR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(CURR_DIR, '../')))
ROOT_DIR = sys.path[-1]


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
        docs = mongo.request_objects_to_regear()

        # STEP[2] importing items dict
        file = f'{ROOT_DIR}/regearbot_package/data/items_dict.json'
        if not os.path.exists(file):
            print('No such file -> items_dict.json')
            return
        else:
            with open(file, 'r') as f:
                items_data = json.load(f)

        # STEP[3] creating dataframe for csv
        temp = {'Name': [],
                'EventId': [],
                'AverageItemPower': [],
                'Items': []}
        for doc in docs:
            temp['Name'].append(doc['Victim'].get('Name'))
            temp['EventId'].append(f"https://albiononline.com/en/killboard/kill/{doc.get('EventId')}")
            temp['AverageItemPower'].append(doc['Victim'].get('AverageItemPower'))

            equipment = doc['Victim'].get('Equipment')
            if equipment:
                for item in equipment:
                    for k, v in item.items():
                        temp['Items'].append(items_data[v])

            inventory = doc['Victim'].get('Inventory')
            if inventory:
                for item in inventory:
                    temp['Items'].append(items_data[item])

        df = pd.DataFrame(temp)

        # STEP[4] save as binary (discord file)
        arr = io.BytesIO()
        df.to_csv(arr, index=False, sep=",")
        arr.seek(0)

        mongo.update_none_regeared_objects_to_regeared()

        return discord.File(fp=arr, filename="regear_requests.csv")

    def print_victim_death_list(self):
        pprint(self.victim_info_list)


class MongoDataManager:
    def __init__(self):
        self.client = MongoClient(MONGO_CLIENT.get('client'))
        self.db = self.client.get_database(MONGO_CLIENT.get('db'))
        self.collection = self.db.get_collection(MONGO_CLIENT.get('collection'))

    def upload_objects_to_db(self, victim_object: dict) -> bool:
        # checks EventId, if no object with the same EventId -> Upload
        event_id = victim_object.get('EventId')
        query = self.collection.find_one({"EventId": event_id})

        if query:
            return False
        else:
            self.collection.insert_one(victim_object)
            return True

    def request_objects_to_regear(self) -> list:
        # get all objects where is_regeared = False
        query = {"is_regeared": False}
        cursor = self.collection.find(query)
        docs = list(cursor).copy()
        return docs

    def update_none_regeared_objects_to_regeared(self):
        query = {"is_regeared": False}
        new_values = {"$set": {"is_regeared": True}}
        self.collection.update_many(query, new_values)

    # ----------------- MANAGEMENT DEBUG METHODS -------------------

    def debug_delete_objects_from_db(self, my_query: dict):
        query = self.collection.delete_one(my_query)
        print(query.deleted_count)

    def debug_delete_multiple_objects_from_db(self):
        my_query = {"category": "Victim_to_regear"}
        query = self.collection.delete_many(my_query)
        print(query.deleted_count, " jsons deleted.")

    def debug_get_quantity_of_objects_in_collection(self):
        query = self.collection.count_documents({"category": "Victim_to_regear"})
        print(query)

    def debug_search_object_by_event_id(self, event_id: int) -> bool:
        query = self.collection.find_one({"EventId": event_id})
        return True if query else False

    def debug_set_objects_to_not_regeared(self):
        query = {"is_regeared": True}
        new_values = {"$set": {"is_regeared": False}}
        self.collection.update_many(query, new_values)


def convert_item_codes_to_json():
    folder = f'{ROOT_DIR}/regearbot_package/data/'
    file = folder + 'item_codes_raw.text'
    with open(file, 'r') as f:
        data = f.readlines()

    rank = {
        "Journeyman's": 'T3',
        "Adept's": 'T4',
        "Expert's": 'T5',
        "Master's": 'T6',
        "Grandmaster's": 'T7',
        "Elder's": 't8'
    }

    items_dict = {}
    for item in data:
        temp = item.replace("\n", "").split(':')
        try:
            k = temp[1].replace(" ", "")
            v = temp[2]

            try:
                tier_name = v.split(' ')[1]
                tier_code = rank[tier_name]
            except Exception:
                pass
            else:
                v = v.replace(tier_name, tier_code.capitalize())

            if '@' in k:
                enchant = f' (+{k.split("@")[1]})'
                v = v + enchant
            items_dict.update({k: v})
        except Exception:
            pass

    file = folder + 'items_dict.json'
    with open(file, 'w') as f:
        json.dump(items_dict, f, indent=4)

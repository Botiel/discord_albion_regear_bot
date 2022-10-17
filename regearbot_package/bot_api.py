from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime as dt
import requests
from PIL import Image
from io import BytesIO
import discord
import json
import os
import sys
from pprint import pprint
import pandas as pd
from regearbot_package.mongo_database import MongoDataManager

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
        try:
            response = requests.get(url=url).json()["players"][0].get("Id")
        except Exception as e:
            print(f'\nError: {e} -> Trying to query non existing player!')
        else:
            return response

    @classmethod
    def get_player_info(cls, player_id: str) -> dict:
        url = f"{cls.albion_url}/players/{player_id}"
        return requests.get(url=url).json()

    @classmethod
    def request_death_data_by_event_id(cls, event_id: str) -> dict:
        return requests.get(url=f"https://gameinfo.albiononline.com/api/gameinfo/events/{event_id}").json()

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
    def request_kill_board_by_even_id(cls, event_id: str):
        return f"https://albiononline.com/en/killboard/kill/{event_id}"

    @classmethod
    def convert_images_to_a_single_image(cls, image_list: list) -> discord.File:
        # Requesting images from api
        pillow_imgs = []
        for img in image_list:

            if img == 'https://render.albiononline.com/v1/item/.png':
                continue

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

        arr = BytesIO()
        new_img.save(arr, format='PNG')
        arr.seek(0)
        return discord.File(fp=arr, filename="items.png")


class Victim(BaseModel):
    Name: str
    Id: str
    AllianceName: Optional[str]
    GuildName: Optional[str]
    AverageItemPower: str = None
    Inventory: List
    inventory_as_png: List[str] = []
    Equipment: Any

    def check_inventory(self):  # Checking inventory for "SIEGEHAMMER"
        if not self.Inventory:
            return

        inventory_li = []
        for item in self.Inventory:
            if item:
                if "SIEGEHAMMER" in item.get('Type'):
                    inventory_li.append(item.get('Type'))
        self.Inventory.clear()
        self.Inventory = inventory_li

    def check_equipment(self):
        equipment = []
        equipment_to_ignore = ['Mount', 'Potion', 'Food', 'Bag']
        for k, v in self.Equipment.items():
            if k in equipment_to_ignore:
                continue
            else:
                if v:
                    equipment.append({k: v.get('Type')})
                else:
                    equipment.append({k: ''})
        self.Equipment.clear()
        self.Equipment = equipment

    def convert_items_to_png_string(self):
        if self.Equipment:
            for item in self.Equipment:
                for k, v in item.items():
                    if v != "":
                        temp = {'png': AlbionApi.request_render_item(item=v)}
                    else:
                        temp = {'png': ""}
                    item.update(temp)
                    break

        if self.Inventory:
            for item in self.Inventory:
                self.inventory_as_png.append(AlbionApi.request_render_item(item=item))

    def translate_items(self):

        file = f'{ROOT_DIR}/regearbot_package/data/items_dict.json'
        if not os.path.exists(file):
            print('No such file -> items_dict.json')
            return
        else:
            with open(file, 'r') as f:
                items_data = json.load(f)

        if self.Equipment:
            for item in self.Equipment:
                for k, v in item.items():
                    temp = {}
                    try:
                        temp = {'item_name': items_data[v]}
                    except Exception:
                        temp = {'item_name': ''}
                    finally:
                        item.update(temp)
                        break


class Death(BaseModel):
    submit_date: str = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    category: str = None
    is_regeared: bool = False
    TimeStamp: str
    BattleId: int
    EventId: int
    KillArea: Optional[str]
    Victim: Victim

    def convert_to_dict(self):
        self.Victim.check_inventory()
        self.Victim.check_equipment()
        self.Victim.convert_items_to_png_string()
        self.Victim.translate_items()
        return self.dict()


class ZvzApprovedBuild(BaseModel):
    time_stamp: str = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    role: str = None
    item_power: float = 0.0
    main_hand: str = None
    off_hand: str = None
    helmet: str = None
    chest: str = None
    boots: str = None
    items_as_png: list[str] = []

    def create_zvz_build(self, content: list[str]):
        self.role = content[0]
        self.main_hand = content[1]
        self.off_hand = content[2]
        self.helmet = content[3]
        self.chest = content[4]
        self.boots = content[5]
        self.item_power = float(content[6])

        # reading the items dictionary
        file = f'{ROOT_DIR}/regearbot_package/data/items_dict.json'
        with open(file, 'r') as f:
            data = json.load(f)

        for i in range(1, 6):
            for k, v in data.items():
                if v == content[i]:
                    self.items_as_png.append(AlbionApi.request_render_item(item=k))

    def validate_build_request(self, msg_content: str) -> dict:
        roles = ['dps', 'healer', 'support', 'tank']

        index1 = msg_content.find('[') + 1
        index2 = msg_content.find(']')
        if index1 == 0 or index2 == -1:
            return {'status': False, 'message': 'Missing "[" or "]" in items setup'}

        new_content = msg_content[index1:index2].split(",")
        if len(new_content) < 7:
            return {'status': False, 'message': 'Missing value'}

        if len(new_content) > 7:
            return {'status': False, 'message': 'Too many values'}

        if new_content[0].lower() not in roles:
            return {'status': False, 'message': 'Invalid role assignment'}

        try:
            ip = float(new_content[6])
        except ValueError:
            return {'status': False, 'message': 'ItemPower value is invalid'}

        self.create_zvz_build(content=new_content)
        return {'status': True}


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

            equipment = victim['Victim'].get("Equipment")
            for item in equipment:
                if item.get("png") != "":
                    temp["items_as_png"].append(item.get("png"))

            if victim['Victim'].get("inventory_as_png"):
                temp["items_as_png"].extend(victim['Victim'].get("inventory_as_png"))

            self.display_list.append(temp)

    @classmethod
    def submit_regear_request(cls, event_id: str):
        mongo_client = MongoDataManager()
        death_data = AlbionApi.request_death_data_by_event_id(event_id=event_id)
        data_to_submit = Death(**death_data)
        return mongo_client.upload_objects_to_db(victim_object=data_to_submit.convert_to_dict())

    @classmethod
    def convert_regear_objects_to_csv(cls):

        # STEP[1] Importing objects from mongodb
        mongo = MongoDataManager()
        docs = mongo.request_objects_to_regear()

        # STEP[3] creating dataframe for csv
        temp = {'Name': [],
                'EventId': [],
                'AverageItemPower': [],
                'Head': [],
                'Armor': [],
                'Shoes': [],
                'Cape': [],
                'MainHand': [],
                'OffHand': [],
                'Inventory': [],
                'Date': [],
                'Time': []
                }
        for doc in docs:
            temp['Name'].append(doc['Victim'].get('Name'))
            temp['EventId'].append(f"https://albiononline.com/en/killboard/kill/{doc.get('EventId')}")
            temp['AverageItemPower'].append(doc['Victim'].get('AverageItemPower'))
            temp['Date'].append(doc.get('TimeStamp').split('T')[0])
            temp['Time'].append(doc.get('TimeStamp').split('T')[1].split('.')[0])

            # checking for items in the dictionary, if none -> append empty string
            equipment = doc['Victim'].get('Equipment')
            if equipment:
                for item in equipment:
                    code = ''
                    name = ''
                    for i, key in enumerate(list(item)):
                        if i == 0:
                            code = key
                        if i == 2:
                            name = item[key]
                    temp[code].append(name)

            # checking items in inventory, if none -> append empty string else append a list of the items
            inventory = doc['Victim'].get('Inventory')
            if inventory:
                temp_items = []
                for item in inventory:
                    temp_items.append(item)
                temp['Inventory'].append(temp_items)
            else:
                temp['Inventory'].append('')

        # debug
        # for k, v in temp.items():
        #     print(k, len(v))

        df = pd.DataFrame(temp)

        # STEP[4] save as binary (discord file)
        arr = BytesIO()
        df.to_csv(arr, index=False, sep=",")
        arr.seek(0)

        mongo.update_none_regeared_objects_to_regeared()
        now = dt.now().strftime("%Y-%m-%d")
        return discord.File(fp=arr, filename=f"regear_requests_{now}.csv")

    def print_victim_death_list(self):
        pprint(self.victim_info_list)


def convert_item_codes_to_json():
    folder = f'{ROOT_DIR}/regearbot_package/data/'
    file = folder + 'item_codes_raw.text'
    with open(file, 'r') as f:
        data = f.readlines()

    rank = {
        "Beginner's": '1',
        "Novice's": '2',
        "Journeyman's": '3',
        "Adept's": '4',
        "Expert's": '5',
        "Master's": '6',
        "Grandmaster's": '7',
        "Elder's": '8'
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
                v = v.replace(tier_name, "")
                v = f"{v} {tier_code}"

            if '@' in k:
                enchant = k.split("@")[1]
                v = f"{v}.{enchant}"
            v = v.strip()
            items_dict.update({k: v})
        except Exception:
            pass

    file = folder + 'items_dict.json'
    with open(file, 'w') as f:
        json.dump(items_dict, f, indent=4)

from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime as dt
import json
import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(CURR_DIR, '../')))
ROOT_DIR = sys.path[-1]


class Victim(BaseModel):
    submitDate: str = None
    Name: str
    Id: str
    AllianceName: Optional[str]
    GuildName: Optional[str]
    AverageItemPower: str = None
    Inventory: List
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


class Death(BaseModel):
    category: str = "Victim_to_regear"
    is_regeared: bool = False
    TimeStamp: str
    BattleId: int
    EventId: int
    KillArea: Optional[str]
    Victim: Victim

    def convert_to_dict(self):
        self.Victim.check_inventory()
        self.Victim.check_equipment()
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

        url = "https://render.albiononline.com/v1/item"
        for i in range(1, 6):
            for k, v in data.items():
                if v == content[i]:
                    self.items_as_png.append(f'{url}/{k}.png')

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

# if __name__ == '__main__':
#     li = ['blalalalala', 'grovekeeper', 'any', 'knight helmet', 'guardian armor', 'knight boots', '1232321]
#     x = ZvzApprovedBuild()
#     x.create_zvz_build(content=li)

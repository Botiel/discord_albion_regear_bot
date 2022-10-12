from pydantic import BaseModel
from typing import Any, List, Optional


# queryTimeStamp: str = dt.now().strftime("%Y-%m-%d %H:%M:%S")


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
    build_name: str = None
    main_hand: str = None
    off_hand: str = None
    helmet: str = None
    chest: str = None
    boots: str = None

    def create_zvz_build(self, content: list[str]):
        self.build_name = content[0]
        self.main_hand = content[1]
        self.off_hand = content[2]
        self.helmet = content[3]
        self.chest = content[4]
        self.boots = content[5]


# if __name__ == '__main__':
#     li = ['blalalalala', 'grovekeeper', 'any', 'knight helmet', 'guardian armor', 'knight boots']
#     x = ZvzApprovedBuild()
#     x.create_zvz_build(content=li)

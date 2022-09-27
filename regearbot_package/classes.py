from pydantic import BaseModel
from typing import Any, List, Optional

# queryTimeStamp: str = dt.now().strftime("%Y-%m-%d %H:%M:%S")


class Victim(BaseModel):
    submitDate: str = None
    Name: str
    Id: str
    AllianceName: Optional[str]
    GuildName: Optional[str]
    AverageItemPower: str
    Inventory: List
    Equipment: Any

    def check_inventory(self):
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








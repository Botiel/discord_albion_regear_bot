import json


def main():
    file = 'data/item_codes_raw.text'
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
                enchant = f' (lvl{k.split("@")[1]})'
                v = v + enchant
            items_dict.update({k: v})
        except Exception:
            pass

    with open('data/items_dict.json', 'w') as f:
        json.dump(items_dict, f, indent=4)


if __name__ == '__main__':
    main()

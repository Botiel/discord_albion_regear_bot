# Discord Albion Regear Bot

- Created By: Nuriel(Thebearjew), Victor(Yocttar).
- Github: https://github.com/Botiel
- Assisted by: Tidal albion guild
- Discord channel: https://discord.gg/eThMPjrytA

# 1. How it works

  - You can either run it locally on your machine or on a docker container in the cloud.
  - This bot works with Mongodb: https://cloud.mongodb.com/

# 2. How to use:

- Config file setup:
    1. Change the config_template.py file in the reagerbot_package directory to config.py
    2. inside the config.py you need to insert all the data as listed

# 3. How to deploy the bot:


# 4. Bot Commands:

for users:
  - !player_mmr \<player name>
  - !deaths \<player name>
  - !last_death \<player name>
  - !regear \<event id>


for admins:
  - !pull_regear_requests
  - !pending
  - !zvz_build_instructions
  - !show_builds \<dps, healer, tank, support, any>

# 5. How to create zvz approved build:

  - Example: !add_setup [role,main_hand,off_hand,helmet,chest,boots,item_power]
  1. start with !add_setup command followed by a space bar
  2. build must me enclosed by brackets [ ]
  3. insert values in the same order as in the example\n
  4. if there is no off_hand item, insert: any
  5. number of values inside the brackets must be 7
  6. all values must be comma separated with no spaces (csv style)
  7. roles: dps, healer, tank, support




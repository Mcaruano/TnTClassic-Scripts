import constants
import os
import yaml

"""
Given a string itemName, reads the loot.yaml file to retrieve the ItemID
"""
def generate_item_name_to_id_map():
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)
    lootYamlDataDict = {}
    with open(os.path.join(scriptDir, constants.CONFIG_FOLDER_NAME, constants.LOOT_DATA_FILE_NAME), 'r', encoding='utf-8') as yamlFile:
        lootYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

    itemNameToIDMap = {}
    for itemID in lootYamlDataDict:
        itemNameToIDMap[lootYamlDataDict[itemID]['item-name']] = itemID
    return itemNameToIDMap

"""
During a raid night if a player doesn't have enough Priority DKP for an item, it gets
automatically added to their Lottery. This can cause an item to exist on both Priority
and Lottery configs after the data is processed. This method simply goes through the data
and WARNS about any such duplicates
"""
def warn_if_duplicate_items_from_lottery_were_found(playerYamlDataDict):
    for player in playerYamlDataDict:
        priorityConfig = playerYamlDataDict[player]['priority-lootconfig']
        lotteryConfig = playerYamlDataDict[player]['lottery-lootconfig']
        for itemName in priorityConfig:
            if itemName in lotteryConfig:
                print("[WARN] Duplicate Priority/Lottery entry found. Player: {}, Item: {}".format(player, itemName))

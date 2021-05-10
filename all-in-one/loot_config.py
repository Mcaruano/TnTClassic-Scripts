import aws_utils
import constants
import copy
from datetime import datetime
import general_utils
import json
import os
from progress.bar import IncrementalBar
import yaml

"""
Given a player's name, read their LootConfig data from the player_data.yaml and format it in
a Python Dictionary as expected for the final JSON output (for consumption by the website)
"""
def build_loot_config_list_for_player_for_yaml_from_registry(lootYamlDataDict, playerName, itemRegistry):
    itemConfigForPlayer = []
    for itemIDString in itemRegistry:
        for playerNameKey, quantity in itemRegistry[itemIDString].items():
            if playerNameKey == playerName:
                # Duplicate items are simply represented by multiple entries in the List
                for _ in range(quantity):
                    itemConfigForPlayer.append(lootYamlDataDict[int(itemIDString)]['item-name'])

    return sorted(itemConfigForPlayer)

"""
Takes a given lootList, filters it for items only in the specified contentTier, and returns back a
Dict as expected for the final JSON output (for consumption by the website)

:param lootYamlDataDict: The YAML python dictionary after parsing the loot.yaml file
:param itemNameToIDMap: A simple map of ItemName -> ItemIDs
:param lootList: A list of ItemNames
:param contentTier: The content/raid tier to filter the lootList for (Ex: 'T1', 'T2', etc.)
"""
def build_loot_config_list_for_player_for_specific_content_tier_for_lootconfig_json_from_registry(lootYamlDataDict, itemNameToIDMap, lootList, contentTier):
    itemConfigForPlayer = []
    itemNames = set()

    # The filter() here is filtering all items from the loot.yaml whose 'content-tier' == the desired raidTier ('T1', 'T2', etc)
    lootListForSpecificTier = list(filter(lambda entry: lootYamlDataDict[itemNameToIDMap[entry]]['content-tier'] == contentTier, lootList))
    for itemName in sorted(lootListForSpecificTier):
        if itemName in itemNames:
            for entry in itemConfigForPlayer:
                if entry["ItemName"] == itemName:
                    entry["Quantity"] = entry["Quantity"] + 1
        else:
            itemDataDict = {}
            itemDataDict["ItemName"] = itemName
            itemDataDict["Quantity"] = 1
            itemDataDict["ItemID"] = itemNameToIDMap[itemName]

            itemNames.add(itemName)

            itemConfigForPlayer.append(itemDataDict)
    
    return itemConfigForPlayer

def generate_lootconfig_dict(playerYamlDataDict):
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)
    lootYamlDataDict = {}
    with open(os.path.join(scriptDir, constants.CONFIG_FOLDER_NAME, constants.LOOT_DATA_FILE_NAME), 'r', encoding='utf-8') as yamlFile:
        lootYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)
    itemNameToIDMap = general_utils.generate_item_name_to_id_map()

    lootConfigDict = {}
    lootConfigDict['dateModified'] = datetime.now().strftime("%A, %B %d, %Y")
    lootConfigDict['timeModified'] = datetime.now().strftime("%-I:%M %p")
    lootConfigDict['raiders'] = []

    for player in playerYamlDataDict:
        playerDataDict = {}
        playerDataDict['name'] = player
        playerDataDict['T4_PriorityDKP'] = 0 if 't4-priority-dkp' not in playerYamlDataDict[player] else playerYamlDataDict[player]['t4-priority-dkp']
        playerDataDict['T4_LotteryDKP'] = 0 if 't4-lottery-dkp' not in playerYamlDataDict[player] else playerYamlDataDict[player]['t4-lottery-dkp']
        playerDataDict['class'] = playerYamlDataDict[player]['class']
        playerDataDict['Rank'] = playerYamlDataDict[player]['rank']
        playerDataDict['T4_PriorityConfig'] = build_loot_config_list_for_player_for_specific_content_tier_for_lootconfig_json_from_registry(lootYamlDataDict, itemNameToIDMap, playerYamlDataDict[player]['priority-lootconfig'], "T4")
        playerDataDict['T4_LotteryConfig'] = build_loot_config_list_for_player_for_specific_content_tier_for_lootconfig_json_from_registry(lootYamlDataDict, itemNameToIDMap, playerYamlDataDict[player]['lottery-lootconfig'], "T4")

        lootConfigDict['raiders'].append(playerDataDict)
    return lootConfigDict

"""
In lieu of having actual DB connectivity from the webpage, it's easy enough to just sort the data here by
Priority DKP descending in the meantime
"""
def sort_lootconfig_dict(lootConfigDict, sortKey, sortDescending):
    sortedDict = copy.deepcopy(lootConfigDict)
    # We only want to display Core and Reserve raiders on the LootConfig website
    onlyCoreAndReserveRaiders = list(filter(lambda entry: entry['Rank'] == 'Core Raider' or entry['Rank'] == 'Reserve Raider', sortedDict['raiders']))
    
    raidersEntriesSorted = []
    raidersEntriesSorted.extend(sorted(onlyCoreAndReserveRaiders, key = lambda i: i[sortKey], reverse=sortDescending))
    sortedDict['raiders'] = raidersEntriesSorted
    return sortedDict

"""
In the absence of an actual DB hosting all player data, it's easy enough to simply generate different LootConfig.json
files which are pre-sorted in different ways. The various files that are produced here are:
    LootConfig_T4Priority_Asc.json
    LootConfig_T4Priority_Desc.json
    LootConfig_T4Lottery_Asc.json
    LootConfig_T4Lottery_Desc.json
"""
def generate_all_desired_loot_config_files(scriptDir, outputFileDirectory, lootConfigDict):
    sortedJsonDicts = {
        'LootConfig_T4Priority_Asc.json': sort_lootconfig_dict(lootConfigDict, 'T4_PriorityDKP', False),
        'LootConfig_T4Priority_Desc.json': sort_lootconfig_dict(lootConfigDict, 'T4_PriorityDKP', True),
        'LootConfig_T4Lottery_Asc.json': sort_lootconfig_dict(lootConfigDict, 'T4_LotteryDKP', False),
        'LootConfig_T4Lottery_Desc.json': sort_lootconfig_dict(lootConfigDict, 'T4_LotteryDKP', True)
    }

    for fileName in sortedJsonDicts:
        lootConfigJSONFilePath = os.path.join(outputFileDirectory, fileName)
        with open(lootConfigJSONFilePath, 'w', encoding='utf-8') as jsonFile:
            json.dump(sortedJsonDicts[fileName], jsonFile, ensure_ascii=False)
        
        # Copy the file to ./json/ so it can be picked up by the website
        lootconfigLatestDataDir = os.path.join(scriptDir, 'json')
        os.rename(lootConfigJSONFilePath, os.path.join(lootconfigLatestDataDir, fileName))

def copy_lootconfig_json_files_to_s3(scriptDir):
    progress_bar = IncrementalBar("   Uploading LootConfig JSON files to S3", max=len(list(os.listdir(os.path.join(scriptDir, 'json')))), suffix='%(percent)d%% ')
    for jsonLootConfigFile in os.listdir(os.path.join(scriptDir, 'json')):
        aws_utils.upload_file(os.path.join(scriptDir, 'json', jsonLootConfigFile), constants.AWS_JSON_BUCKET_NAME, jsonLootConfigFile)
        progress_bar.next()
    progress_bar.finish()

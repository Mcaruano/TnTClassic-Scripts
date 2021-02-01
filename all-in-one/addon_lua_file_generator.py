import general_utils
import os

"""
Given the AddOn data as a dictionary, generate the Lua data tables we desire
for the AddOn to begin the next raid week with. This includes only the following tables:
    - T3_PRIORITY_DKP_TABLE
    - T2PT5_PRIORITY_DKP_TABLE
    - T2_PRIORITY_DKP_TABLE
    - T1_PRIORITY_DKP_TABLE
    - T3_LOTTERY_DKP_TABLE
    - T2PT5_LOTTERY_DKP_TABLE
    - T2_LOTTERY_DKP_TABLE
    - T1_LOTTERY_DKP_TABLE
    - PLAYER_PRIORITY_REGISTRY
    - PLAYER_LOTTERY_REGISTRY
"""
def generate_latest_addon_lua_file_from_player_data(playerYamlDataDict, outputFilePath):
    with open(outputFilePath, "w", encoding='utf-8') as f:
        f.write('T3_PRIORITY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't3-priority-dkp')
        f.write('}\n')

        f.write('T2PT5_PRIORITY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't2pt5-priority-dkp')
        f.write('}\n')

        f.write('T2_PRIORITY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't2-priority-dkp')
        f.write('}\n')

        f.write('T1_PRIORITY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't1-priority-dkp')
        f.write('}\n')

        f.write('T3_LOTTERY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't3-lottery-dkp')
        f.write('}\n')

        f.write('T2PT5_LOTTERY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't2pt5-lottery-dkp')
        f.write('}\n')

        f.write('T2_LOTTERY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't2-lottery-dkp')
        f.write('}\n')

        f.write('T1_LOTTERY_DKP_TABLE = {\n')
        print_dkp_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 't1-lottery-dkp')
        f.write('}\n')

        # Output the Priority and Lottery LootConfig/Registries
        f.write('PLAYER_PRIORITY_REGISTRY = {\n')
        print_lootconfig_records_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 'priority-lootconfig')
        f.write('}\n')

        f.write('PLAYER_LOTTERY_REGISTRY = {\n')
        print_lootconfig_records_from_yaml_for_key_to_file_as_lua_table(f, playerYamlDataDict, 'lottery-lootconfig')
        f.write('}\n')


"""
For each player, retrieves the LootConfig as designated by the lootconfigKey from the
playerYamlDataDict and writes it into Lua table format.
"""
def print_lootconfig_records_from_yaml_for_key_to_file_as_lua_table(outputFile, playerYamlDataDict, lootconfigKey):
    itemNameToIDMap = general_utils.generate_item_name_to_id_map()
    # Build the lootConfigDict from the playerYamlDataDict
    lootConfigDict = {}
    for player in playerYamlDataDict:
        if not playerYamlDataDict[player][lootconfigKey]:
            continue
        for itemName in playerYamlDataDict[player][lootconfigKey]:
            itemID = itemNameToIDMap[itemName]
            if itemID not in lootConfigDict:
                lootConfigDict[itemID] = {}

            lootConfigDict[itemID][player] = 1 if player not in lootConfigDict[itemID] else lootConfigDict[itemID][player] + 1

    # Output the records to the file in Lua format
    for itemID in lootConfigDict:
        outputFile.write("	[{}] = {{\n".format(int(itemID)))

        for player in lootConfigDict[itemID].keys():
            outputFile.write('		["{}"] = {},\n'.format(player, lootConfigDict[itemID][player]))

        outputFile.write("	},\n")

'''
For each player, retrieves the DKP value as designated by the dkpKey from the
playerYamlDataDict and writes it into Lua table format.
'''
def print_dkp_from_yaml_for_key_to_file_as_lua_table(outputFile, playerYamlDataDict, dkpKey):
    for player in playerYamlDataDict:
        outputFile.write('   ["{}"] = {},\n'.format(player, 0 if dkpKey not in playerYamlDataDict[player] else playerYamlDataDict[player][dkpKey]))


def generate_addon_roster_files(outputFileDirectory, playerYamlDataDict):
    with open(os.path.join(outputFileDirectory, 'ReserveRaidRoster.lua'), 'w', encoding='utf-8') as f:
        f.write('reserveRaiders = {\n')
        index = 1
        for player in playerYamlDataDict:
            if playerYamlDataDict[player]['rank'] == 'Reserve Raider':
                f.write('	[{}] = "{}",\n'.format(index, player))
                index += 1
        f.write('}\n')
    
    with open(os.path.join(outputFileDirectory, 'MainRaidRoster.lua'), 'w', encoding='utf-8') as f:
        f.write('mainRaiders = {\n')
        index = 1
        for player in playerYamlDataDict:
            if playerYamlDataDict[player]['rank'] == 'Core Raider':
                f.write('	[{}] = "{}",\n'.format(index, player))
                index += 1
        f.write('}\n')


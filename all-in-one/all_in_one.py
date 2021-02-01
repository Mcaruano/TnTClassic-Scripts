# coding=utf-8

import addon_lua_file_generator
import addon_output_parser
import archive_file_generator
import bank_inventory_parser
import constants
import data_merger
from datetime import datetime
import general_utils
import loot_config
import os
import sys
import yaml

"""
Our definition of "all known members" for the purposes of this script is simply "all members
who are present on either our Priority or Lottery DKP lists." Logic dictates that it should
be impossible for a player to be on one of these lists without also being on the other, but
we take the extra precaution.
"""
def build_set_of_all_members(addonDkpDataDict):
    members = set()
    for member in addonDkpDataDict['T1_PRIORITY_DKP_TABLE'].keys():
        members.add(member)

    for member in addonDkpDataDict['T1_LOTTERY_DKP_TABLE'].keys():
        members.add(member)
    
    if 'T2_PRIORITY_DKP_TABLE' in addonDkpDataDict:
        for member in addonDkpDataDict['T2_PRIORITY_DKP_TABLE'].keys():
            members.add(member)

    if 'T2_LOTTERY_DKP_TABLE' in addonDkpDataDict:
        for member in addonDkpDataDict['T2_LOTTERY_DKP_TABLE'].keys():
            members.add(member)

    if 'T2PT5_PRIORITY_DKP_TABLE' in addonDkpDataDict:
        for member in addonDkpDataDict['T2PT5_PRIORITY_DKP_TABLE'].keys():
            members.add(member)

    if 'T2PT5_LOTTERY_DKP_TABLE' in addonDkpDataDict:
        for member in addonDkpDataDict['T2PT5_LOTTERY_DKP_TABLE'].keys():
            members.add(member)

    if 'T3_PRIORITY_DKP_TABLE' in addonDkpDataDict:
        for member in addonDkpDataDict['T3_PRIORITY_DKP_TABLE'].keys():
            members.add(member)

    if 'T3_LOTTERY_DKP_TABLE' in addonDkpDataDict:
        for member in addonDkpDataDict['T3_LOTTERY_DKP_TABLE'].keys():
            members.add(member)
    
    return members

"""
Given the latest DKP standings and LootConfigs from the AddOn output, regenerate the player_data.yaml file
"""
def generate_new_player_yaml_file(outputFilePath, existingPlayerYamlDataDict, addonDataDict):
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)
    lootYamlDataDict = {}
    with open(os.path.join(scriptDir, constants.CONFIG_FOLDER_NAME, constants.LOOT_DATA_FILE_NAME), 'r', encoding='utf-8') as yamlFile:
        lootYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

    allMembers = build_set_of_all_members(addonDataDict)
    newPlayerYamlDataDict = existingPlayerYamlDataDict
    for player in allMembers:
        if player not in newPlayerYamlDataDict:
            newPlayerYamlDataDict[player] = {}
            newPlayerYamlDataDict[player]['class'] = "Not Set"
            newPlayerYamlDataDict[player]['rank'] = "Not Set"

        newPlayerYamlDataDict[player]['t1-priority-dkp'] = 0 if ('T1_PRIORITY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T1_PRIORITY_DKP_TABLE']) else addonDataDict['T1_PRIORITY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t1-lottery-dkp'] = 0 if ('T1_LOTTERY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T1_LOTTERY_DKP_TABLE']) else addonDataDict['T1_LOTTERY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t2-priority-dkp'] = 0 if ('T2_PRIORITY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T2_PRIORITY_DKP_TABLE']) else addonDataDict['T2_PRIORITY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t2-lottery-dkp'] = 0 if ('T2_LOTTERY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T2_LOTTERY_DKP_TABLE']) else addonDataDict['T2_LOTTERY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t2pt5-priority-dkp'] = 0 if ('T2PT5_PRIORITY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T2PT5_PRIORITY_DKP_TABLE']) else addonDataDict['T2PT5_PRIORITY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t2pt5-lottery-dkp'] = 0 if ('T2PT5_LOTTERY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T2PT5_LOTTERY_DKP_TABLE']) else addonDataDict['T2PT5_LOTTERY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t3-priority-dkp'] = 0 if ('T3_PRIORITY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T3_PRIORITY_DKP_TABLE']) else addonDataDict['T3_PRIORITY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['t3-lottery-dkp'] = 0 if ('T3_LOTTERY_DKP_TABLE' not in addonDataDict or player not in addonDataDict['T3_LOTTERY_DKP_TABLE']) else addonDataDict['T3_LOTTERY_DKP_TABLE'][player]
        newPlayerYamlDataDict[player]['priority-lootconfig'] = loot_config.build_loot_config_list_for_player_for_yaml_from_registry(lootYamlDataDict, player, addonDataDict['PLAYER_PRIORITY_REGISTRY'])
        newPlayerYamlDataDict[player]['lottery-lootconfig'] = loot_config.build_loot_config_list_for_player_for_yaml_from_registry(lootYamlDataDict, player, addonDataDict['PLAYER_LOTTERY_REGISTRY'])

    # Delete the existing player_data.yaml file
    if os.path.isfile(outputFilePath):
        os.remove(outputFilePath)

    # Write the new player_data.yaml file
    with open(outputFilePath, 'w', encoding='utf-8') as playerYamlFile:
        yaml.dump(newPlayerYamlDataDict, playerYamlFile, allow_unicode=True)
    
    return newPlayerYamlDataDict

"""
Moves the file at the given path to the trash/ directory
"""
def move_file_to_trash_dir(scriptDir, fileName, filePath):
    # Generate the "trash/" directory if it doesn't exist
    trashFileDirectory = os.path.join(scriptDir, constants.TRASH_FOLDER_NAME)
    if not os.path.exists(trashFileDirectory):
        os.makedirs(trashFileDirectory)
    
    # Move the file to the trash directory
    os.rename(filePath, os.path.join(trashFileDirectory, fileName))

if __name__ == "__main__":
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)

    playerYamlDataDict = {}
    with open(os.path.join(scriptDir, constants.CONFIG_FOLDER_NAME, constants.PLAYER_DATA_FILE_NAME), 'r', encoding='utf-8') as yamlFile:
        playerYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

    addonDataDict = {}
    didProcessNewAddonDKPData = False

    # Generate the "gen/" directory if it doesn't exist
    outputFileDirectory = os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME)
    if not os.path.exists(outputFileDirectory):
        os.makedirs(outputFileDirectory)

    # Parse and process output frmo the TnTCharacterBankSnapshotter.lua file if it's present
    bankSnapshotterLuaFilePath = os.path.join(scriptDir, constants.RAW_FOLDER_NAME, constants.BANK_SNAPSHOTTER_LUA_FILE_NAME)
    if os.path.isfile(bankSnapshotterLuaFilePath):
        bankSnapshotDataDict = bank_inventory_parser.parse_bank_snapshot_to_dict(bankSnapshotterLuaFilePath)
        bankInventoryJsonDataDict = bank_inventory_parser.generate_bank_inventory_json_data_dict(scriptDir, bankSnapshotDataDict)
        bank_inventory_parser.generate_bank_inventory_json_data_file(scriptDir, outputFileDirectory, bankSnapshotDataDict)
        move_file_to_trash_dir(scriptDir, constants.BANK_SNAPSHOTTER_LUA_FILE_NAME, bankSnapshotterLuaFilePath)

    # Merge AddOn Output if unmerged data is present. Move the unmerged data files to trash/ when done
    didProcessMergedData = False
    inputLuaFilePath = os.path.join(scriptDir, constants.RAW_FOLDER_NAME, constants.INPUT_LUA_FILE_NAME)
    masterLuaFilePath = os.path.join(scriptDir, constants.RAW_FOLDER_NAME, constants.MASTER_LUA_FILE_NAME)
    if os.path.isfile(inputLuaFilePath):
        if not os.path.isfile(masterLuaFilePath):
            print("[ERROR] TnTDKP_input.lua was present but a corresponding TnTDKP.lua file was not. We are not going to make assumptions about how to process this data. Exiting.")
            sys.exit(1)
    
        inputDataDict = addon_output_parser.parse_addon_lua_file_to_dict(inputLuaFilePath)
        masterDataDict = addon_output_parser.parse_addon_lua_file_to_dict(masterLuaFilePath)
        addonDataDict = data_merger.merge_addon_data(inputDataDict, masterDataDict)
        move_file_to_trash_dir(scriptDir, constants.INPUT_LUA_FILE_NAME, inputLuaFilePath)
        move_file_to_trash_dir(scriptDir, constants.MASTER_LUA_FILE_NAME, masterLuaFilePath)
        didProcessNewAddonDKPData = True

    # Parse the output from a "complete" AddOn output file (one that does not need to be merged)
    addonOutputLuaFilePath = os.path.join(scriptDir, constants.RAW_FOLDER_NAME, constants.ADDON_OUTPUT_LUA_DATA_FILE_NAME)
    if os.path.isfile(addonOutputLuaFilePath):
        addonDataDict = addon_output_parser.parse_addon_lua_file_to_dict(addonOutputLuaFilePath)
        didProcessNewAddonDKPData = True
        move_file_to_trash_dir(scriptDir, constants.ADDON_OUTPUT_LUA_DATA_FILE_NAME, addonOutputLuaFilePath)

    # If we processed new AddOn data during this run, we need to update the YamlDataDict and generate an Archive file
    archiveFileName = None
    if didProcessNewAddonDKPData:

        # Regenerate player_data.yaml with updated LootConfigs & DKP Standings from the AddOn output
        playerYamlDataDict = generate_new_player_yaml_file(os.path.join(scriptDir, constants.CONFIG_FOLDER_NAME, constants.PLAYER_DATA_FILE_NAME), playerYamlDataDict, addonDataDict)

        # Generate the file which we will copy to the TnTClassic-Archive git repository
        archiveFileName = archive_file_generator.generate_archive_lua_file_from_addon_data(addonDataDict, os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME))

    # Warn about detected duplicate entries from players' Lottery and Priority LootConfigs
    general_utils.warn_if_duplicate_items_from_lottery_were_found(playerYamlDataDict)

    # Generate latest addon data from LootConfig and DKP data with a name of the following format: "TnTDKPData_10_22_2019-17_33.lua"
    todaysDateAsString = datetime.now().strftime("%m_%d_%Y-%H_%M")
    latestAddonDataFileName = 'TnTDKPData_{}.lua'.format(todaysDateAsString)
    addon_lua_file_generator.generate_latest_addon_lua_file_from_player_data(playerYamlDataDict, os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME, latestAddonDataFileName))

    # Generate the desired LootConfigs (we have different LootConfigs for each sorting)
    lootConfigDict = loot_config.generate_lootconfig_dict(playerYamlDataDict)
    loot_config.generate_all_desired_loot_config_files(scriptDir, outputFileDirectory, lootConfigDict)

    loot_config.copy_lootconfig_json_files_to_s3(scriptDir)

    # Generate ReserveRaidRoster.lua and MainRaidRoster.lua files
    addon_lua_file_generator.generate_addon_roster_files(outputFileDirectory, playerYamlDataDict)

    # If we processed new AddOn data, that means we generated a new Archive file. After doing so, we take a quick look
    # to see if the TnTClassic-Archive/ git repository is colocated in the same directory as this repo. If it
    # is, we go ahead and copy the generated Archive file over
    repoDir = os.path.abspath(os.path.join(scriptDir, os.pardir))
    if didProcessNewAddonDKPData:
        outerDir = os.path.abspath(os.path.join(repoDir, os.pardir))
        if os.path.exists(os.path.join(outerDir, 'TnTClassic-Archive')):
            generatedArchiveFilePath = os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME, archiveFileName)
            addonArchiveGitRepoFilePath = os.path.join(outerDir, 'TnTClassic-Archive', archiveFileName)
            os.rename(generatedArchiveFilePath, addonArchiveGitRepoFilePath)
            print("- {} was copied over to: {}".format(archiveFileName, addonArchiveGitRepoFilePath))
        else:
            print("- {} needs to be copied to the TnTClassic-Archive git repository.".format(archiveFileName))

    # Each run of this script always generates a new AddOn data file as well as ReserveRaidRoster.lua and
    # MainRaidRoster.lua files. Similar to the above logic, we take a quick look to see if the TnTDKP/
    # git repository is colocated in the same directory as this one, and copy the artifacts over automatically if so
    outerDir = os.path.abspath(os.path.join(repoDir, os.pardir))
    addonLatestDataFetchDirPath = os.path.join(outerDir, 'TnTDKP', 'latest_data_fetch')
    if os.path.exists(addonLatestDataFetchDirPath):
        # Clear out any files currently in the 'latest_data_fetch/' directory of the TnTDKP repo
        for filename in os.listdir(addonLatestDataFetchDirPath):
            filePath = os.path.join(addonLatestDataFetchDirPath, filename)
            try:
                if os.path.isfile(filePath) or os.path.islink(filePath):
                    os.unlink(filePath)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (filePath, e))

        # Copy over the latest AddOn data file        
        generatedAddonDataFilePath = os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME, latestAddonDataFileName)
        addonLatestDataGitRepoFilePath = os.path.join(addonLatestDataFetchDirPath, latestAddonDataFileName)
        os.rename(generatedAddonDataFilePath, addonLatestDataGitRepoFilePath)
        print("- {} was copied over to: {}".format(latestAddonDataFileName, addonLatestDataGitRepoFilePath))

        # Copy over the ReserveRaidRoster.lua file
        generatedReserveRaidRosterFilePath = os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME, 'ReserveRaidRoster.lua')
        addonReserveRosterGitRepoFilePath = os.path.join(outerDir, 'TnTDKP', 'TnTDKP', 'ReserveRaidRoster.lua')
        os.rename(generatedReserveRaidRosterFilePath, addonReserveRosterGitRepoFilePath)
        print("- ReserveRaidRoster.lua was copied over to: {}".format(addonReserveRosterGitRepoFilePath))

        # Copy over the MainRaidRoster.lua file
        generatedMainRaidRosterFilePath = os.path.join(scriptDir, constants.GENERATED_ARTIFACTS_FOLDER_NAME, 'MainRaidRoster.lua')
        addonMainRosterGitRepoFilePath = os.path.join(outerDir, 'TnTDKP', 'TnTDKP', 'MainRaidRoster.lua')
        os.rename(generatedMainRaidRosterFilePath, addonMainRosterGitRepoFilePath)
        print("- MainRaidRoster.lua was copied over to: {}".format(addonMainRosterGitRepoFilePath))
    else:
        print("- {} needs to be copied to the \"latest_data_fetch/\" directory of the TnTDKP repository.".format(latestAddonDataFileName))
        print("- MainRaidRoster.lua and ReserveRaidRoster.lua need to be copied to the \"TnTDKP/\" directory of the TnTDKP repository.")
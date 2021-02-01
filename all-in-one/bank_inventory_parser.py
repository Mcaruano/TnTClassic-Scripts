# coding=utf-8

import constants
from datetime import datetime
import json
import math
import os
import re
import yaml

"""
Parse the Bank snapshot from the file and read it into a Dict of the following format:
{
    'Tntbank':
        {
            13040: 1,
            17011: 19,
            ...
            14504: 1,
            0: 4307920
        },

    'Tntauctions':
        {
            13040: 1,
            17011: 19,
            ...
            14504: 1,
            0: 4307920
        },
}
where the Key is the ItemID, and the value is the Quantity.
NOTE: The record with ItemID of 0 represents the money (in Copper) on the character
"""
def parse_bank_snapshot_to_dict(bankSnapshotFilePath):
    f = open(bankSnapshotFilePath, "r")
    lines = f.readlines()
    f.close()
    
    bankSnapshotDataDict = {}
    dictKeyStack = []
    for line in lines:

        # The BankContent records are in the following format:
        # BankContents = {
        # 	["Tntauctions"] = {
        # 		"16804,1", -- [1]
        # 		"16857,1", -- [2]
        # 		"7078,5", -- [3]
        # 		"0,2589338", -- [4]
        # 	},
        # 	["Tntbank"] = {
        # 		"11979,2", -- [1]
        # 		"11370,118", -- [2]
        # 		"17010,30", -- [3]
        # 		 ......
        # 		"15410,20", -- [16]
        # 		"17011,34", -- [17]
        # 		"0,21173977", -- [18]
        # 	},
        # }
        #

        # This pattern matches keys of the format "["Tntauctions"] = {"
        if re.search("\[\"[a-zA-Z]+\"\] = {", line) is not None:
            # This pulls out just the character name - "Tntauctions" in the example entry shown above
            characterName = re.search("[a-zA-Z]+", line).group()
            bankSnapshotDataDict[characterName] = {}
            dictKeyStack.append(characterName)
            continue

        # If this condition is met, we've reached the end of the current entry of a Table
        # Example:
        # 	["Tntauctions"] = {
        # 		"16804,1", -- [1]
        # 		"16857,1", -- [2]
        # 		"7078,5", -- [3]
        # 		"0,2589338", -- [4]
        # 	},
        if re.search("},", line) is not None:
            # "pop" the last key from the end of the dictKeyStack
            dictKeyStack = dictKeyStack[:-1]
            continue

        # This pattern matches the "13040,1" value, and trims off the leading " and trailing ",
        if re.search("\".*\",", line) is not None:
            record = re.search("\".*\",", line).group()[1:-2]
        
            # Split the record by "," and load it into a Dict
            values = record.split(',')
            itemID = int(values[0])
            quantity = int(values[1])

            # Insert this data into the dict for the current key
            bankSnapshotDataDict[dictKeyStack[-1]][itemID] = quantity

    return bankSnapshotDataDict

"""
Takes the raw dictionary which was generated from reading the AddOn output and generates a completely new
dictionary, structured as expected for outputting to the BankInventory.json file
"""
def generate_bank_inventory_json_data_dict(scriptDir, bankSnapshotDataDict):
    bankItemYamlDataDict = {}
    with open(os.path.join(scriptDir, constants.CONFIG_FOLDER_NAME, constants.BANK_ITEM_DATA_FILE_NAME), 'r', encoding='utf-8') as yamlFile:
        bankItemYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

    bankInventoryDict = {}
    bankInventoryDict['dateModified'] = datetime.now().strftime("%A, %B %d, %Y")
    bankInventoryDict['timeModified'] = datetime.now().strftime("%-I:%M %p")

    totalCopperOnAllChars = bankSnapshotDataDict['Tntbank'][0] + bankSnapshotDataDict['Tntauctions'][0]

    if 'Tntbanktwo' in bankSnapshotDataDict:
        totalCopperOnAllChars += bankSnapshotDataDict['Tntbanktwo'][0]

    bankInventoryDict['totalGold'] = math.floor(totalCopperOnAllChars/10000)
    
    bankInventoryDict['itemsBeingStocked'] = []
    bankInventoryDict['itemsBeingSold'] = []

    # Items on the 'Tntauctions' character are items which we are actively seeking to sell on the AH
    for itemID in sorted(bankSnapshotDataDict['Tntauctions'], reverse=False):
        # Character Gold is accounted for elsewhere in this method
        if itemID == 0:
            continue
        itemInfoDict = {}
        itemInfoDict['ItemID'] = itemID
        itemInfoDict['Quantity'] = bankSnapshotDataDict['Tntauctions'][itemID]
        bankInventoryDict['itemsBeingSold'].append(itemInfoDict)

    # Items on the 'Tntbank' character are items which we are keeping in stock
    for itemID in sorted(bankSnapshotDataDict['Tntbank'], reverse=False):
        # Character Gold is accounted for elsewhere in this method
        if itemID == 0:
            continue
        itemInfoDict = {}
        itemInfoDict['ItemID'] = itemID
        itemInfoDict['Quantity'] = bankSnapshotDataDict['Tntbank'][itemID]
        bankInventoryDict['itemsBeingStocked'].append(itemInfoDict)

    # Items on the 'Tntbanktwo' character are also items which we are keeping in stock
    if 'Tntbanktwo' in bankSnapshotDataDict:    
        for itemID in sorted(bankSnapshotDataDict['Tntbanktwo'], reverse=False):
            # Character Gold is accounted for elsewhere in this method
            if itemID == 0:
                continue

            # If this itemID is already present in Tntbank's inventory, we simply incremenet the quantity
            indexOfMatch = find_index_of_record_if_exists(bankInventoryDict, itemID)
            if indexOfMatch > -1:
                bankInventoryDict['itemsBeingStocked'][indexOfMatch]['Quantity'] += bankSnapshotDataDict['Tntbanktwo'][itemID]
            else:
                itemInfoDict = {}
                itemInfoDict['ItemID'] = itemID
                itemInfoDict['Quantity'] = bankSnapshotDataDict['Tntbanktwo'][itemID]
                bankInventoryDict['itemsBeingStocked'].append(itemInfoDict)

    return bankInventoryDict

"""
Iterates over the 'itemsBeingStocked' List in the bankInventoryDict to determine if a record already exists for the
given itemID. If so, it returns the index. If not, it returns -1
"""
def find_index_of_record_if_exists(bankInventoryDict, itemID):
    index = 0
    for itemRecord in bankInventoryDict['itemsBeingStocked']:
        if itemRecord['ItemID'] == itemID:
            return index
        index += 1
    
    return -1

"""
Takes the dictionary containing bank inventory data, structures it as it should be, and writes it to
the BankInventory.lua
"""
def generate_bank_inventory_json_data_file(scriptDir, outputFileDirectory, bankSnapshotDataDict):
    # Process the bankSnapshotDataDict to be of the JSON format we want
    bankInventoryJSONFilePath = os.path.join(outputFileDirectory, 'BankInventory.json')
    with open(bankInventoryJSONFilePath, 'w', encoding='utf-8') as jsonFile:
        json.dump(generate_bank_inventory_json_data_dict(scriptDir, bankSnapshotDataDict), jsonFile, ensure_ascii=False)
    
    # Copy the file to ./json/ so it can be picked up by the website
    jsonDataDir = os.path.join(scriptDir, 'json')
    os.rename(bankInventoryJSONFilePath, os.path.join(jsonDataDir, 'BankInventory.json'))


# coding=utf-8

# This script uses the DKP data contained in the "original_data/TnTDKP.lua" file and uses it
# to perform the "squish" to determine the seeding for the upcoming raid tier. The output
# of this calculation is a .yaml file with the new PRIORITY and LOTTERY DKP standings of the
# upcoming raid tier already formatted in the way I need to just copy and paste them into
# the player_data.yaml file

from datetime import datetime
import os
import re
import sys


ORIGINAL_DATA_FOLDER_NAME = "original_data"
INPUT_LUA_DATA_FILE_NAME = "TnTDKP.lua"

OUTPUT_DATA_FOLDER_NAME = "output"
OUTPUT_LUA_DATA_FILE_NAME = "TnTDKP_squished.yaml"

PRIORITY_DKP_TARGET = 3750
LOTTERY_DKP_TARGET = 3750

PREVIOUS_RAID_TIER = "T5"
NEXT_RAID_TIER = "T6"

"""
Parses a LUA file into a python dictionary. The Dictionary structure is as follows:
    {
      'LOTTERY_DKP_TABLE': 
        {
          'Akaran': 2400,
           'Anarra': 2500,

           ...

           'Zeion': 0,
           'Ziddy': 1650
        },
    }
"""
def parse_addon_lua_file_to_dict(filePath):
    f = open(filePath, "r")
    lines = f.readlines()
    f.close()

    dataDict = {}
    dictKeyStack = []
    dataDict['ITEMS_RECEIVED'] = {}
    dataDict['ITEMS_RECEIVED']['PRIORITY'] = {}
    dataDict['ITEMS_RECEIVED']['LOTTERY'] = {}
    for line in lines:
        # If this line is the variable declaration of a LUA variable, parse the name.
        # Regex matches strings such as "PLAYER_PRIORITY_REGISTRY" or "STANDBYEP"
        if re.search("[A-Z]+(_[A-Z]+)* = ", line) is not None:

            # For T6.5, I have variable names which don't follow the standard LUA variable pattern. This prepends
            # a (T6)* onto the front of the pattern to capture T6PT5_* variable names.
            variableName = re.search("(T6)*[A-Z]+[0-9]*(_[A-Z]+)* = ", line).group()[:-3]
            dataDict[variableName] = {}

            # The only variables I care about parsing are all Tables. Table variables always have a "{" bracket
            if re.search("{", line) is not None:
                # Append this key to the dictKeyStack
                dictKeyStack.append(variableName)

                # If we're dealing with the TRANSACTIONS records, we need to instantiate a list instead of a dict
                if variableName.endswith("_TRANSACTIONS"):
                    dataDict[variableName] = []
                else:
                    dataDict[variableName] = {}
                continue

        # This pattern matches keys of the format "[16864] = {", which represents an entry in a Registry table
        if re.search("\[[0-9]+\] = {", line) is not None:
            # This pulls out just the itemID - "16864" in the example entry shown above
            tableKey = re.search("[0-9]+", line).group()
            dataDict[dictKeyStack[-1]][tableKey] = {}
            dictKeyStack.append(tableKey)
            continue

        # If this condition is met, we've reached the end of the current entry of a Table, or the end of a transaction record.
        # Examples:
        #     [18806] = {
        #         ["Akaran"] = 1,
        #     },
        #            -OR-
        #     {
        #         "Iopo", -- [1]
        #         "Nocjr", -- [2]
        #         "[DKP +25]: on time", -- [3]
        #         1425, -- [4]
        #         1450, -- [5]
        #         "", -- [6]
        #         "03551598920298475579", -- [7]
        #         "Tue Oct 22 18:56:22 2019", -- [8]
        #     }, -- [1]
        # }
        if re.search("},", line) is not None:
            if not dictKeyStack[-1].endswith("_TRANSACTIONS"):
                # "pop" the last key from the end of the dictKeyStack
                dictKeyStack = dictKeyStack[:-1]
                continue

        # If this condition is met (no comma), we've reached the end of a Variable definition block. Variable
        # blocks never have trailing commas.
        elif re.search("}", line) is not None:
            # "pop" the last key from the end of the dictKeyStack
            dictKeyStack = dictKeyStack[:-1]
            continue

        # Otherwise, we are dealing with a data record for the current Lua Table object.
        # The structure of each record varies depending on what variable we are parsing.
        parse_data_record(dataDict, dictKeyStack, line)

    return dataDict

"""
Different Lua Table entries have different structures for their data. We handle
each of these unique cases here
"""
def parse_data_record(dataDict, dictKeyStack, data_record):
    if len(dictKeyStack) <= 0:
        print("Attempted to parse line but dictKeyStack was empty. Line contents: {}".format(data_record))
        return
    currentKey = dictKeyStack[-1]

    # Example structure of a _DKP_TABLE entry:
    # PRIORITY_DKP_TABLE = {
    #     ["Noxyqt"] = 1600,
    # }
    if currentKey.endswith("_DKP_TABLE"):
        # Parse the player name. Due to dumbasses using special characters in their names,
        # we have to match the entire "UserName" block and trim off the quotes
        playerName = re.search("\".*\"", data_record).group()[1:-1]
        dkp = int(re.search("-?[0-9]+", data_record).group())
        dictForItemID = dataDict[dictKeyStack[-1]]
        dictForItemID[playerName] = dkp     

def calculate_and_execute_squish(addonDataDict):
    previousPriorityTableKey = '{}_PRIORITY_DKP_TABLE'.format(PREVIOUS_RAID_TIER)
    previousLotteryTableKey = '{}_LOTTERY_DKP_TABLE'.format(PREVIOUS_RAID_TIER)
    # Determine who has the highest Priority DKP
    highestPriorityDKPRecord = sorted(addonDataDict[previousPriorityTableKey].items(), key=lambda item: item[1], reverse=True)[0]
    print("PRIORITY - Highest {} DKP record is: {}".format(PREVIOUS_RAID_TIER, highestPriorityDKPRecord))

    # Determine the factor to scale the Priority DKP by
    priorityScalar = PRIORITY_DKP_TARGET / highestPriorityDKPRecord[1]
    print("PRIORITY - Squish Scaling Factor = {}".format(priorityScalar))

    # Scale all Priority DKP values by the Priority scaling factor, using a precision of 2 decimal places
    for player in addonDataDict[previousPriorityTableKey]:
        addonDataDict[previousPriorityTableKey][player] = '{:.2f}'.format(addonDataDict[previousPriorityTableKey][player] * priorityScalar)


    # Determine who has the highest Lottery DKP
    highestLotteryDKPRecord = sorted(addonDataDict[previousLotteryTableKey].items(), key=lambda item: item[1], reverse=True)[0]
    print("LOTTERY - Highest {} DKP record is: {}".format(PREVIOUS_RAID_TIER, highestLotteryDKPRecord))

    # Determine the factor to scale the Lottery DKP by
    lotteryScalar = LOTTERY_DKP_TARGET / highestLotteryDKPRecord[1]
    print("LOTTERY - Squish Scaling Factor = {}".format(lotteryScalar))

    # Scale all Lottery DKP values by the Lottery scaling factor, using a precision of 2 decimal places
    for player in addonDataDict[previousLotteryTableKey]:
        if addonDataDict[previousLotteryTableKey][player] < 0:
            print("{} had negative Lottery DKP, not squishing".format(player))
        else:
            addonDataDict[previousLotteryTableKey][player] = '{:.2f}'.format(addonDataDict[previousLotteryTableKey][player] * lotteryScalar)
    
    return addonDataDict

'''
Transforms the given dkpDict into Lua table format, printing each entry to
the provided filestream.
'''
def print_dkp_to_file_as_lua_table(outputFile, dkpDict):
    for player in dkpDict:
        outputFile.write('   ["{}"] = {},\n'.format(player,dkpDict[player]))


def print_new_dkp_values_to_yaml_format(mergedDataDict, outputFile):
    previousPriorityTableKey = '{}_PRIORITY_DKP_TABLE'.format(PREVIOUS_RAID_TIER)
    previousLotteryTableKey = '{}_LOTTERY_DKP_TABLE'.format(PREVIOUS_RAID_TIER)
    upcomingRaidTierPriorityYamlKey = "{}-priority-dkp".format(NEXT_RAID_TIER.lower())
    upcomingRaidTierLotteryYamlKey = "{}-lottery-dkp".format(NEXT_RAID_TIER.lower())


    with open(outputFilePath, "w") as outputFile:
        for player in sorted(mergedDataDict[previousPriorityTableKey]):
            outputFile.write('{}:\n'.format(player))
            outputFile.write('  {}: {}\n'.format(upcomingRaidTierPriorityYamlKey, mergedDataDict[previousPriorityTableKey][player]))
            outputFile.write('  {}: {}\n'.format(upcomingRaidTierLotteryYamlKey, mergedDataDict[previousLotteryTableKey][player]))



if __name__ == "__main__":
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)

    inputFilePath = os.path.join(scriptDir, ORIGINAL_DATA_FOLDER_NAME, INPUT_LUA_DATA_FILE_NAME)
    addonDataDictBeforeSquish = parse_addon_lua_file_to_dict(inputFilePath)

    addonDataDictAfterSquish = calculate_and_execute_squish(addonDataDictBeforeSquish)

    # Generate the output directory if it doesn't exist
    outputFileDirectory = os.path.join(scriptDir, OUTPUT_DATA_FOLDER_NAME)
    if not os.path.exists(outputFileDirectory):
        os.makedirs(outputFileDirectory)
    outputFilePath = os.path.join(outputFileDirectory, OUTPUT_LUA_DATA_FILE_NAME)
    print_new_dkp_values_to_yaml_format(addonDataDictAfterSquish, outputFilePath)

    sys.exit(0)






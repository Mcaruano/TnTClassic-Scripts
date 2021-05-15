# coding=utf-8
# This is a Utility script which takes in a TierNLoot.lua file and converts it to the output we need for the "config/loot.yaml" file.
# Generating new records in the loot.yaml file is necessary when we introduce new raid tiers.
#
# DISCLAIMER: This script is just a general down-and-dirty utility to get a simple job done. It is not written to be elegant or easily-run
# on other machines.

import constants
from datetime import datetime
import json
import math
import os
import re
import yaml

CONTENT_TIER = "T4"
LUA_FILE_PATH = "/Users/Melanie/Git Repositories/TnTDKP/TnTDKP/TierFourLoot.lua"
OUTPUT_FILE_PATH = "/Users/Melanie/Git Repositories/TnTClassic-Scripts/all-in-one/TierFourLoot.yaml"

"""
Parses a loot LUA file of the following format:
    tierOneLoot = {
        -- Trash drops
        [1] = 16864, -- Belt of Might
        [2] = 16861, -- Bracers of Might
    }
... and generates a YAML file of the loot in the following format:
    19364:
    content-tier: {CONTENT_TIER}
    item-name: Ashkandi, Greatsword of the Brotherhood
    19434:
    content-tier: {CONTENT_TIER}
    item-name: Band of Dark Dominion
"""
def parse_loot_lua_file_to_dict():
    f = open(LUA_FILE_PATH, "r")
    lines = f.readlines()
    f.close()
    
    newContentTierLootDataDict = {}
    for line in lines:

        # This pattern matches the "[1] = " lines, which are the only ones we care about
        if re.search("\[[0-9]+\] =", line) is not None:
            itemID = int(re.search("[0-9]+,", line).group()[:-1])
            itemName = re.search("-- .*", line).group()[3:]

            newContentTierLootDataDict[itemID] = {}
            newContentTierLootDataDict[itemID]['content-tier'] = CONTENT_TIER
            newContentTierLootDataDict[itemID]['item-name'] = itemName

    return newContentTierLootDataDict

if __name__ == "__main__":
    newContentTierLootDataDict = parse_loot_lua_file_to_dict()

    # Write the new player_data.yaml file
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as playerYamlFile:
        yaml.dump(newContentTierLootDataDict, playerYamlFile, allow_unicode=True)

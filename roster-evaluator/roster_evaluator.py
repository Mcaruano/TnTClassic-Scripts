# coding=utf-8

# TODO

import bisect
from datetime import datetime
from discord_name_mapping import resolveName
from specific_roster_callouts import SPECIFIC_ROSTER_CALLOUTS
import os
import re
import sys
import yaml

ALL_IN_ONE_CONFIG_FOLDER_NAME = 'config'
PLAYER_DATA_FILE_NAME = 'player_data.yaml'
LOOT_FILE_NAME = 'loot.yaml'
INPUT_DATA_FOLDER_NAME = "raw_roster_paste"
INPUT_DATA_FILE_NAME = "roster.txt"
OUTPUT_FOLDER_NAME = "output"
OUTPUT_FILE_NAME = "roster_evaluation.txt"

DATE_KEY = "DATE"
TIER_KEY = "RAID"
NUM_TANKS_KEY = "NUM_TANKS"
NUM_HEALERS_KEY = "NUM_HEALERS"
NUM_DPS_KEY = "NUM_DPS"
NUM_ALTS_KEY = "NUM_ALTS"
NUM_SITS_KEY = "NUM_SITS"
NUM_ACTIVE_SIGNUPS_KEY = "NUM_ACTIVE_SIGNUPS"
NUM_LATE_SIGNUPS_KEY = "NUM_LATE_SIGNUPS"
NUM_BENCH_SIGNUPS_KEY = "NUM_BENCH_SIGNUPS"
NUM_TENTATIVE_SIGNUPS_KEY = "NUM_TENTATIVE_SIGNUPS"
NUM_ABSENT_SIGNUPS_KEY = "NUM_ABSENT_SIGNUPS"
MISSING_PLAYERS_KEY = "MISSING_PLAYERS"
PROPOSED_SITS_KEY = "PROPOSED_SITS"
MUST_KEEP_KEY = "MUST_KEEP"

IS_BENCH_KEY = "IsBench"
IS_TENTATIVE_KEY = "IsTentative"
IS_ABSENT_KEY = "IsAbsent"
CLASS_SIGNED_UP_KEY = "ClassSignedUpAs"
IS_ALT_KEY = "IsAlt"
IS_SOCIAL_KEY = "IsSocial"
ROLE_KEY = "Role"
PRIO_NEXT_UP_LIST_KEY = "PrioNextUpList"
PRIO_SECOND_UP_LIST_KEY = "PrioSecondUpList"
LOTTERY_ODDS_LIST_KEY = "LotteryOddsList"

'''
Parse the raw roster.txt file and saturate the raidData and playerData dicts. Only the
"IsBench", "IsTentative", "Role", and "ClassSignedUpAs" playerData keys will be saturated here.
'''
def parse_raw_roster_input_and_saturate_dicts(filePath, playerYamlDataDict):
    f = open(filePath, "r")
    lines = f.readlines()
    f.close()

    playerData = {}

    raidData = {}
    raidData[DATE_KEY] = "TBD"
    raidData[TIER_KEY] = "Unknown"
    raidData[NUM_DPS_KEY] = 0
    raidData[NUM_TANKS_KEY] = 0
    raidData[NUM_HEALERS_KEY] = 0
    raidData[NUM_LATE_SIGNUPS_KEY] = 0
    raidData[NUM_BENCH_SIGNUPS_KEY] = 0
    raidData[NUM_TENTATIVE_SIGNUPS_KEY] = 0
    raidData[NUM_ABSENT_SIGNUPS_KEY] = 0
    raidData[MISSING_PLAYERS_KEY] = []
    raidData[PROPOSED_SITS_KEY] = []
    raidData[MUST_KEEP_KEY] = []

    for line in lines:
        # This matches the Regional Indicators which are what RaidHelper uses when creating event titles
        if re.search("Karazhan", line) is not None or re.search("Gruul", line) is not None or re.search("Mag", line) is not None:
            raidData[TIER_KEY] = "T4"
        
        # Date is in the format: "Thu 2. Sep"
        if re.search(":CMcalendar:", line) is not None:
            raidData[DATE_KEY] = re.search("[A-Za-z]+ [0-9]+. [A-Za-z]+", line).group()

        if re.search(":signups: [0-9]+", line) is not None:
            raidData[NUM_ACTIVE_SIGNUPS_KEY] = int(re.search("[0-9]+", line).group())
        
        if re.search("^:Tanks: [0-9]+ - Melee - [0-9]+ :Dps:", line) is not None:
            raidData[NUM_TANKS_KEY] = int(re.search(":Tanks: [0-9]+", line).group()[8:])
            raidData[NUM_DPS_KEY] += int(re.search("[0-9]+ :Dps:", line).group()[:-6])

        if re.search("^:Ranged: Ranged - [0-9]+ :Ranged:", line) is not None:
            raidData[NUM_DPS_KEY] += int(re.search("[0-9]+", line).group())

        if re.search("^:Healers: Healers - [0-9]+ :Healers:", line) is not None:
            raidData[NUM_HEALERS_KEY] = int(re.search("[0-9]+", line).group())

        if re.search("^:Late: Late \([0-9]+\) :", line) is not None:
            raidData[NUM_LATE_SIGNUPS_KEY] = int(re.search("[0-9]+", line).group())
            latePlayers = re.search("[0-9]+ .+,", line, re.DOTALL).group() # This looks like: "5 Zoff, :Warrior: 7 Zerxx, :Mage: 29 Nynisa,"
            for match in latePlayers[:-1].split(','): # The [:-1] slices off the trailing ',' before the split()
                discordName = match.split(' ')[-1] # Each entry will be of the format: "34 Zoff" or ":Warrior: 7 Zerxx", so we split on ' ' and take the last item
                playerName = resolveName(discordName)
                isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
                playerData[playerName] = {}
                playerData[playerName] = instantiate_player_record(playerData[playerName], "N/A", "N/A", True, False, False, False, isSocial)

        if re.search("^:Bench: Bench \([0-9]+\) :", line) is not None:
            raidData[NUM_BENCH_SIGNUPS_KEY] = int(re.search("[0-9]+", line).group())
            benchPlayers = re.search("[0-9]+ .+,", line, re.DOTALL).group() # This looks like: "5 Zoff, :Warrior: 7 Zerxx, :Mage: 29 Nynisa,"
            for match in benchPlayers[:-1].split(','): # The [:-1] slices off the trailing ',' before the split()
                discordName = match.split(' ')[-1] # Each entry will be of the format: "34 Zoff" or ":Warrior: 7 Zerxx", so we split on ' ' and take the last item
                playerName = resolveName(discordName)
                isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
                playerData[playerName] = {}
                playerData[playerName] = instantiate_player_record(playerData[playerName], "N/A", "N/A", True, False, False, False, isSocial)
                
        if re.search("^:Tentative: Tentative \([0-9]+\) :", line) is not None:
            raidData[NUM_TENTATIVE_SIGNUPS_KEY] = int(re.search("[0-9]+", line).group())
            tentativePlayers = re.search("[0-9]+ .+,", line, re.DOTALL).group() # This looks like: "5 Zoff, :Warrior: 7 Zerxx, :Mage: 29 Nynisa,"
            for match in tentativePlayers[:-1].split(','): # The [:-1] slices off the trailing ',' before the split()
                discordName = match.split(' ')[-1] # Each entry will be of the format: "34 Zoff" or ":Warrior: 7 Zerxx", so we split on ' ' and take the last item
                playerName = resolveName(discordName)
                isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
                playerData[playerName] = {}
                playerData[playerName] = instantiate_player_record(playerData[playerName], "N/A", "N/A", False, True, False, False, isSocial)
            
        if re.search("^:Absence: Absence \([0-9]+\) :", line) is not None:
            raidData[NUM_ABSENT_SIGNUPS_KEY] = int(re.search("[0-9]+", line).group())
            absentPlayers = re.search("[0-9]+ .+,", line, re.DOTALL).group() # This looks like: "5 Zoff, :Warrior: 7 Zerxx, :Mage: 29 Nynisa,"
            for match in absentPlayers[:-1].split(','): # The [:-1] slices off the trailing ',' before the split()
                discordName = match.split(' ')[-1] # Each entry will be of the format: "34 Zoff" or ":Warrior: 7 Zerxx", so we split on ' ' and take the last item
                playerName = resolveName(discordName)
                isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
                playerData[playerName] = {}
                playerData[playerName] = instantiate_player_record(playerData[playerName], "N/A", "N/A", False, False, True, False, isSocial)
        
        if re.search("^:Protection: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Warrior"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Protection", "Tank", False, False, False, isAlt, isSocial)

        if re.search("^:Arms: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Warrior"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Arms", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Fury: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Warrior"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Fury", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Beastmastery: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Hunter"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Beastmastery", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Marksman: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Hunter"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Marksman", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Survival: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Hunter"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Survival", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Discipline: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Priest"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Discipline", "Healer", False, False, False, isAlt, isSocial)

        if re.search("^:Holy: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Priest"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Holy", "Healer", False, False, False, isAlt, isSocial)

        if re.search("^:Shadow: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Priest"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Shadow", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Fire: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Mage"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Fire", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Frost: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Mage"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Frost", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Arcane: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Mage"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Arcane", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Protection1: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Paladin"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Protection1", "Tank", False, False, False, isAlt, isSocial)

        if re.search("^:Holy1: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Paladin"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Holy1", "Healer", False, False, False, isAlt, isSocial)

        if re.search("^:Retribution: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Paladin"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Retribution", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Combat: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Rogue"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Combat", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Subtlety: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Rogue"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Subtlety", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Assassination: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Rogue"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Assassination", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Affliction: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Warlock"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Affliction", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Demonology: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Warlock"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Demonology", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Destruction: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Warlock"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Destruction", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Guardian: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Druid"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Guardian", "Tank", False, False, False, isAlt, isSocial)

        if re.search("^:Restoration: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Druid"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Restoration", "Healer", False, False, False, isAlt, isSocial)
        
        if re.search("^:Feral: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Druid"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Feral", "DPS", False, False, False, isAlt, isSocial)
        
        if re.search("^:Balance: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Druid"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Balance", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Restoration1: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Shaman"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Restoration1", "Healer", False, False, False, isAlt, isSocial)

        if re.search("^:Elemental: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Shaman"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Elemental", "DPS", False, False, False, isAlt, isSocial)

        if re.search("^:Enhancement: [0-9]+", line) is not None:
            discordName = line.split(' ')[2][:-1] # [:-1] shaves off the newline character
            playerName = resolveName(discordName)
            isSocial = (playerName not in playerYamlDataDict) or playerYamlDataDict[playerName]["rank"] != "Core Raider" or playerYamlDataDict[playerName]["rank"] != "Reserve Raider"
            if playerName not in playerYamlDataDict:
                isAlt = False
            else:
                isAlt = playerYamlDataDict[playerName]["class"] != "Shaman"
            playerData[playerName] = {}
            playerData[playerName] = instantiate_player_record(playerData[playerName], "Enhancement", "DPS", False, False, False, isAlt, isSocial)
        
    # 1.) Evaluate the line after the "Leader" line to determine which raid tier this is for (for LootConfig lookups)
        # Aggregate this as well as a few other items into a RaidData dictionary, containing the following:
            # - Content tier
            # - Number of Tanks
            # - Number of healers
            # - Number of DPS
            # - Number of Active Roster signups
            # - Number of Bench signups
            # - Number of Tentative Signups

    ######## Dictionary structure will end up as follows ########
        # Player:
        #     - IsBench: True/False
        #     - IsTentative: True/False
        #     - IsAbsent: True/False
        #     - ClassSignedUpAs: Hunter|Mage|etc - # This is referring to the Discord "Reaction" that the player used to indicate which class they signed up as
        #     - IsAlt: True/False - # If this is true, the PrioNextUp and LotteryOdds lists will contain data for the main
        #     - IsSocial: True/False - # Just used for determining roster priority
        #     - Role: "Tank"|"Healer"|"DPS"
        #     - PrioNextUp: ["Item1", "Item2"] or []
        #     - LotteryOdds: [("ItemA", 98.1234), ("ItemB", 3.2988)] or []


    return raidData, playerData

'''
Instantiates a player record of the playerData dict with the values provided
'''
def instantiate_player_record(playerDict, classSignedUpAs, role, isBench, isTentative, isAbsent, isAlt, isSocial):
    playerDict[IS_BENCH_KEY] = isBench
    playerDict[IS_TENTATIVE_KEY] = isTentative
    playerDict[IS_ABSENT_KEY] = isAbsent
    playerDict[IS_ALT_KEY] = isAlt
    playerDict[IS_SOCIAL_KEY] = isSocial
    playerDict[CLASS_SIGNED_UP_KEY] = classSignedUpAs
    playerDict[ROLE_KEY] = role
    playerDict[PRIO_NEXT_UP_LIST_KEY] = []
    playerDict[PRIO_SECOND_UP_LIST_KEY] = []
    playerDict[LOTTERY_ODDS_LIST_KEY] = []

    return playerDict


def perform_evaluation(raidData, discordAttendeePlayerData, playerYamlDataDict):
    # 0.) Check if Content Tier is "Unknown". If so, error out and figure out why
    if raidData[TIER_KEY] == "Unknown":
        print("[ERROR] There was an error determining the raid tier. Check the roster.txt file.")
        sys.exit(1)

    # 1.)
    # Identify who is missing from the signups. This only cares about Core and Reserve raiders who have failed to sign up.
    allPlayersOnTheSignup = set(discordAttendeePlayerData.keys())
    # Remove the players who marked 
    absentPlayers = set(filter(lambda playerName: discordAttendeePlayerData[playerName][IS_ABSENT_KEY], discordAttendeePlayerData))
    playersSignedUp = allPlayersOnTheSignup.difference(absentPlayers)

    # Missing Players is the subset of all known players minus those who signed up minus those who marked absent
    allKnownPlayers = set()
    for playerName in playerYamlDataDict.keys():
        if playerYamlDataDict[playerName]["rank"] == "Core Raider" or playerYamlDataDict[playerName]["rank"] == "Reserve Raider":
            allKnownPlayers.add(playerName)
    missingPlayers = allKnownPlayers.difference(playersSignedUp).difference(absentPlayers)
    raidData[MISSING_PLAYERS_KEY] = list(missingPlayers)
    print("The following players are missing from the signups: {}".format(missingPlayers)) # TODO: Remove this print and bake it into the report

    # 2.)
    # Aggregate a list of people who are on Alts and a list of the Social signups
    altPlayers = set()
    socialPlayers = set()
    for playerName in discordAttendeePlayerData.keys():
        if discordAttendeePlayerData[playerName][IS_ALT_KEY]:
            altPlayers.add(playerName)
        elif discordAttendeePlayerData[playerName][IS_SOCIAL_KEY]:
            socialPlayers.add(playerName)
    raidData[NUM_ALTS_KEY] = len(altPlayers)

    # UP-FRONT CHECK. If the Active Signups + Tentative Signups + Bench Signups + Missing Signups are <= 40, we do NOT need to perform all of the evaluations that follow.
    # HOWEVER, we should still perform an "alt & bench sanity" check to confirm that the players on alts and the players on the bench
    # aren't up for a piece of loot.
    if raidData[NUM_ACTIVE_SIGNUPS_KEY] + raidData[NUM_TENTATIVE_SIGNUPS_KEY] + raidData[NUM_BENCH_SIGNUPS_KEY] + len(raidData[MISSING_PLAYERS_KEY]) <= 25:
        raidData[NUM_SITS_KEY] = 0
        # TODO: Perform Alt & Bench sanity check
        return raidData, discordAttendeePlayerData
        
    raidData[NUM_SITS_KEY] = raidData[NUM_ACTIVE_SIGNUPS_KEY] + raidData[NUM_TENTATIVE_SIGNUPS_KEY] + raidData[NUM_BENCH_SIGNUPS_KEY] + len(raidData[MISSING_PLAYERS_KEY]) - 25
    
    # Pull in all items for this tier (using the TIER_KEY) key. Will need to pull this data from the loot.yaml file
    # Iterate over all members, and all items on each member's LootConfigs. Compare each item to see if it's loot for this raid tier and if it is, add this ITEM
    # to a new Dictionary of Lists, and add the PLAYER to this item's list
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)


    # Load the loot.yaml file from the all-in-one/ repo
    repoDir = os.path.abspath(os.path.join(scriptDir, os.pardir))
    allInOneGitRepoFilePath = os.path.join(repoDir, 'all-in-one', ALL_IN_ONE_CONFIG_FOLDER_NAME, LOOT_FILE_NAME)
    lootYamlDataDict = {}
    with open(os.path.join(allInOneGitRepoFilePath), 'r', encoding='utf-8') as yamlFile:
        lootYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

    # We want to restrict the following evaluations to only pertain to loot for the raid we're evaluating
    lootForThisTier = set()
    for itemID in lootYamlDataDict.keys():
        if lootYamlDataDict[itemID]['content-tier'] == raidData[TIER_KEY]:
            lootForThisTier.add(lootYamlDataDict[itemID]['item-name'])
    
    # Create a dict of lists containing all items desired by players at Priority, and a list of who desires them
    possiblePriorityLoot = {}
    for playerName in discordAttendeePlayerData.keys():
        if playerName in playerYamlDataDict:
            for priorityItem in playerYamlDataDict[playerName]['priority-lootconfig']:
                if priorityItem in lootForThisTier:
                    if priorityItem in possiblePriorityLoot:
                        possiblePriorityLoot[priorityItem].append(playerName)
                    else:
                        possiblePriorityLoot[priorityItem] = [playerName]

    # Create a dict of lists containing all items desired by players at Lottery, and a list of who desires them
    possibleLotteryLoot = {}
    for playerName in discordAttendeePlayerData.keys():
        if playerName in playerYamlDataDict:        
            for lotteryItem in playerYamlDataDict[playerName]['lottery-lootconfig']:
                if lotteryItem in lootForThisTier:
                    if lotteryItem in possibleLotteryLoot:
                        possibleLotteryLoot[lotteryItem].append(playerName)
                    else:
                        possibleLotteryLoot[lotteryItem] = [playerName]
            # We also want to include players who have this item on Priority so that the logic will be able to take
            # into acccount players who might not be able to afford it at Priority and will end up needing to roll
            # for it in the Lottery
            for priorityItem in playerYamlDataDict[playerName]['priority-lootconfig']:
                if priorityItem in lootForThisTier:
                    if priorityItem in possibleLotteryLoot:
                        possibleLotteryLoot[priorityItem].append(playerName)
                    else:
                        possibleLotteryLoot[priorityItem] = [playerName]

    # 3.) Iterate over the Core/Reserve raiders and perform the following for each:
        # Determine if they are next up for any of their Priority loot (based on those attending)
        # Determine their odds for Each item on their Lottery (based on those attending) [USE VERY HIGH PRECISION]
        # If they have 0 for both Priority AND Lottery, then they are instantly candidates for sitting. Add them to their own list though for tracking
    prioDkpKeys = {'T4': 't4-priority-dkp', 'T5': 't5-priority-dkp', 'T6': 't6-priority-dkp', "T6.5": 't6pt5-priority-dkp'}
    lotteryDkpKeys = {'T4': 't4-lottery-dkp', 'T5': 't5-lottery-dkp', 'T6': 't6-lottery-dkp', "T6.5": 't6pt5-lottery-dkp'}
    for coreOrReserveMember in playersSignedUp:

        # This is the logic block for performing the Lottery evaluation for this player
        for lotteryItem in playerYamlDataDict[coreOrReserveMember]['lottery-lootconfig']:

            # We only want to evaluate loot for this content tier
            if lotteryItem not in possibleLotteryLoot: continue

            odds = determine_odds_for_lottery_item(playerYamlDataDict, raidData[TIER_KEY], lotteryDkpKeys, coreOrReserveMember, possibleLotteryLoot[lotteryItem])

            # Insert this as a tuple in the player's ODDS_LIST, and do it 
            bisect.insort(discordAttendeePlayerData[coreOrReserveMember][LOTTERY_ODDS_LIST_KEY], (odds, lotteryItem))
            
        # After we've finished evaluating the odds for each of the given player's Lottery items, the result will be
        # stored in a list of tuples (via the bisect library), but will be sorted ASC. We want this list sorted DESC,
        # so we simply reverse it here
        discordAttendeePlayerData[coreOrReserveMember][LOTTERY_ODDS_LIST_KEY].reverse()

        # Up-front check to see if they even have enough Prio DKP for ANYTHING from this tier.
        # If they aren't this check bypasses the Priority evaluation logic block below
        if not player_can_afford_prio_item(playerYamlDataDict, coreOrReserveMember, raidData[TIER_KEY], prioDkpKeys): continue
        
        # This is the logic block for performing the Priority evaluation for this player
        for priorityItem in playerYamlDataDict[coreOrReserveMember]['priority-lootconfig']:

            # We only want to evaluate loot for this content tier
            if priorityItem not in possiblePriorityLoot: continue

            # Among all attending players who want the given item at Priority, determine the top two with priority DKP
            highestPrioWinner, secondHighestPrioWinner = determine_highest_prio_winners_for_item(playerYamlDataDict, raidData[TIER_KEY], prioDkpKeys, possiblePriorityLoot[priorityItem])
            # If the player is next up or second-in-line for the given item at Priority, add the item to their corresponding List
            if coreOrReserveMember == highestPrioWinner:
                discordAttendeePlayerData[coreOrReserveMember][PRIO_NEXT_UP_LIST_KEY].append(priorityItem)
            elif coreOrReserveMember == secondHighestPrioWinner:
                discordAttendeePlayerData[coreOrReserveMember][PRIO_SECOND_UP_LIST_KEY].append(priorityItem)

    # 4.) Based on the above evaluation, pull out only the subset of those players who are NOT up for an item at Priority.
        # In this new subset, associate each player with the item on Lottery which they have the HIGHEST odds at
        # Sort this subset by this highest-odds value, ascending (lowest odds at top)
        # This will actually constitute the list of players who should be sat.
    playersNotUpForPriorityItems = set(filter(lambda playerName: not discordAttendeePlayerData[playerName][PRIO_NEXT_UP_LIST_KEY], discordAttendeePlayerData))
    playersNotUpForPriorityItems.difference_update(absentPlayers) # Take the above set and subtract out those who marked Absent

    potentialCandidatesForSitting = [] # This will be a list of Tuples of Tuples of the format (<odds>, (<playerName>, <itemName>))
    for player in playersNotUpForPriorityItems:
        if not discordAttendeePlayerData[player][LOTTERY_ODDS_LIST_KEY]:
            bisect.insort(potentialCandidatesForSitting, (0, (player, "Has nothing on Lottery")))
        else:
            # Find the first eligible item to be recieved at Lottery in this player's desired Lottery LootConfig
            highestOddsLotteryItem = "Nothing"
            highestLotteryItemOdds = 0
            for odds, itemName in discordAttendeePlayerData[player][LOTTERY_ODDS_LIST_KEY]:
                
                # Once we've found an item to record, break out
                if highestOddsLotteryItem != "Nothing": break

                if itemName in possiblePriorityLoot:
                    highestPrioWinner, _ = determine_highest_prio_winners_for_item(playerYamlDataDict, raidData[TIER_KEY], prioDkpKeys, possiblePriorityLoot[itemName])
                    if highestPrioWinner == "Not Set":
                        highestOddsLotteryItem = itemName
                        highestLotteryItemOdds = odds
                else:
                    highestOddsLotteryItem = itemName
                    highestLotteryItemOdds = odds

            # If no potential Lottery item was identified for this player, insert a record indicating so
            if highestOddsLotteryItem == "Nothing":
                # Just because it was determined that the player cannot win anything on Lottery does not mean the player
                # had nothing on Lottery. We want to set the correct message based on this fact
                if len(discordAttendeePlayerData[player][LOTTERY_ODDS_LIST_KEY]) > 0:
                    bisect.insort(potentialCandidatesForSitting, (0, (player, "Can't win any of their Lottery items")))
                else:
                    bisect.insort(potentialCandidatesForSitting, (0, (player, "Has nothing on Lottery")))
            else:
                bisect.insort(potentialCandidatesForSitting, (highestLotteryItemOdds, (player, highestOddsLotteryItem)))

    # Consider now the Zero-Odds candidates from step 3, and the sorted Ascending Lottery odds from Step 4, and check the roles of these players
    proposedCandidatesForSitting = []
    for odds, playerAndItemRecord in potentialCandidatesForSitting:
        if odds <= 100:
            proposedCandidatesForSitting.append((odds, playerAndItemRecord))
    raidData[PROPOSED_SITS_KEY] = proposedCandidatesForSitting

    # Aggregate the list of players who we must keep due to them being up for loot
    # Begin with the players with high odds for Lottery
    mustKeepPlayers = []
    for odds, playerAndItemRecord in potentialCandidatesForSitting:
        if odds >= 50:
            mustKeepPlayers.append(("LOTTERY", odds, playerAndItemRecord))

    # Then aggregate the list of players who are next up for items at Priority
    playersUpForPrioItems = allKnownPlayers
    playersUpForPrioItems.difference_update(playersNotUpForPriorityItems)
    playersUpForPrioItems.difference_update(absentPlayers)
    playersUpForPrioItems.difference_update(missingPlayers)
    if playersUpForPrioItems is not None:
        for player in playersUpForPrioItems:
            for prioItemName in discordAttendeePlayerData[player][PRIO_NEXT_UP_LIST_KEY]:
                mustKeepPlayers.append(("PRIORITY", 100.00, (player, prioItemName)))
    raidData[MUST_KEEP_KEY] = mustKeepPlayers

    return raidData, discordAttendeePlayerData

"""
Simply confirms whether or not the player has enough Priority DKP to even take an item at Priority
for the given Content Tier.
"""
def player_can_afford_prio_item(playerYamlDataDict, playerName, contentTier, prioDkpKeys):
    itemCosts = {'T4': 1000, 'T5': 2000, 'T6': 3000, "T6.5": 4000}
    return playerYamlDataDict[playerName][prioDkpKeys[contentTier]] >= itemCosts[contentTier]

"""
Given a list of players and a given content tier, return the two players with the highest
priority DKP in that content tier
"""
def determine_highest_prio_winners_for_item(playerYamlDataDict, contentTier, prioDkpKeys, playersToCompare):
    highestPrioPlayer = "Not Set"
    highestPrioDKP = 0
    secondHighestPrioPlayer = "Not Set"
    secondHighestPrioDKP = 0
    
    for player in playersToCompare:
        if not player_can_afford_prio_item(playerYamlDataDict, player, contentTier, prioDkpKeys): continue

        # Check this player's DKP against the current first-in-line player
        if playerYamlDataDict[player][prioDkpKeys[contentTier]] > highestPrioDKP:
            if highestPrioPlayer == "Not Set":
                highestPrioPlayer = player
                highestPrioDKP = playerYamlDataDict[player][prioDkpKeys[contentTier]]

            # If the current highest player is Core, then the current player must be a Core Raider to surpass them in line
            elif playerYamlDataDict[highestPrioPlayer]["rank"] == "Core Raider":

                # If the player being evaluated is also Core, then this check doesn't matter, and the player is the new highestPrioPlayer
                if playerYamlDataDict[player]["rank"] == "Core Raider":
                    secondHighestPrioPlayer = highestPrioPlayer
                    secondHighestPrioDKP = highestPrioDKP
                    highestPrioPlayer = player
                    highestPrioDKP = playerYamlDataDict[player][prioDkpKeys[contentTier]]
                # Otherwise, if the player being evaluated is Reserve and they can't unseat the highestPrioPlayer, perform the same check against the secondHighestPrioPlayer
                else:
                    if secondHighestPrioPlayer == "Not Set":
                        secondHighestPrioPlayer = player
                        secondHighestPrioDKP = playerYamlDataDict[player][prioDkpKeys[contentTier]]
                    # If the secondHighestPrioPlayer is also a Core raider then the player being evaluated is not in the top 2 for this item
                    elif playerYamlDataDict[secondHighestPrioPlayer]["rank"] == "Core Raider":
                        continue
                    # If the secondHighestPrioPlayer is a Reserve raider then the player being evaluated overtakes their spot as secondHighestPrioPlayer
                    else:
                        secondHighestPrioPlayer = player
                        secondHighestPrioDKP = playerYamlDataDict[player][prioDkpKeys[contentTier]]
            # If the current highest player is NOT Core, then this player can freely assume the role of highestPrioPlayer
            else:
                secondHighestPrioPlayer = highestPrioPlayer
                secondHighestPrioDKP = highestPrioDKP
                highestPrioPlayer = player
                highestPrioDKP = playerYamlDataDict[player][prioDkpKeys[contentTier]]

        # Check this player's DKP against the current second-in-line player               
        elif playerYamlDataDict[player][prioDkpKeys[contentTier]] > secondHighestPrioDKP:
            secondHighestPrioPlayer = player
            secondHighestPrioDKP = playerYamlDataDict[player][prioDkpKeys[contentTier]]

    return (highestPrioPlayer, secondHighestPrioPlayer)

"""
Determine the given player's odds at winning a lottery against the set of other players who want the same item, using
their DKP for the given content tier.
"""
def determine_odds_for_lottery_item(playerYamlDataDict, contentTier, lotteryDkpKeys, playerToComputeOddsFor, allPlayersInLottery):
    if len(allPlayersInLottery) == 1: return 100
    totalTicketsInLottery = 0
    for player in allPlayersInLottery:
        playerLotteryDKP = playerYamlDataDict[player][lotteryDkpKeys[contentTier]]
        if playerLotteryDKP > 0:
            totalTicketsInLottery += round(playerLotteryDKP)
        else:
            totalTicketsInLottery += 1
        
    playerToComputeOddsForDKP = playerYamlDataDict[playerToComputeOddsFor][lotteryDkpKeys[contentTier]] if playerYamlDataDict[playerToComputeOddsFor][lotteryDkpKeys[contentTier]] > 0 else 1
    
    return round(100*(playerToComputeOddsForDKP / totalTicketsInLottery), 2)

"""
- Active Signups: 
- Bench Signups: 
- Tentative Signups: 
- Players who Marked Absent: 
- Players Missing from the Signup:
- Number of Tanks: 
- Number of Healers: 
- Number of Alts: 
- Number of Players that need to sit: 
"""
def generate_report_file(scriptDir, updatedRaidData, updatedPlayerData):

    # Generate the output directory if it doesn't exist
    outputFileDirectory = os.path.join(scriptDir, OUTPUT_FOLDER_NAME)
    if not os.path.exists(outputFileDirectory):
        os.makedirs(outputFileDirectory)
    outputFilePath = os.path.join(outputFileDirectory, OUTPUT_FILE_NAME)

    with open(outputFilePath, "w") as f:

        f.write('**__Roster Summary for {}__**\n'.format(updatedRaidData[DATE_KEY]))
        f.write('**Active Signups:** {}\n'.format(updatedRaidData[NUM_ACTIVE_SIGNUPS_KEY]))
        f.write('**Bench Signups:** {} {}\n'.format(updatedRaidData[NUM_BENCH_SIGNUPS_KEY], list(filter(lambda playerName: updatedPlayerData[playerName][IS_BENCH_KEY], updatedPlayerData))))
        f.write('**Tentative Signups:** {} {}\n'.format(updatedRaidData[NUM_TENTATIVE_SIGNUPS_KEY], list(filter(lambda playerName: updatedPlayerData[playerName][IS_TENTATIVE_KEY], updatedPlayerData))))
        f.write('**Players Who Marked Absent:** {} {}\n'.format(updatedRaidData[NUM_ABSENT_SIGNUPS_KEY], list(filter(lambda playerName: updatedPlayerData[playerName][IS_ABSENT_KEY], updatedPlayerData))))
        f.write("**Players who haven't hit the signup yet:** {} {}\n".format(len(updatedRaidData[MISSING_PLAYERS_KEY]), updatedRaidData[MISSING_PLAYERS_KEY]))
        f.write('-\n')
        f.write('**Number of Tanks:** {}\n'.format(updatedRaidData[NUM_TANKS_KEY]))
        f.write('**Number of Healers:** {}\n'.format(updatedRaidData[NUM_HEALERS_KEY]))
        f.write('**Number of Alts:** {} {}\n'.format(updatedRaidData[NUM_ALTS_KEY], list(filter(lambda playerName: updatedPlayerData[playerName][IS_ALT_KEY], updatedPlayerData))))

        f.write('**Number of Players *Potentially* needing to be Sat:** {}\n'.format(updatedRaidData[NUM_SITS_KEY]))
        
        # Write the "Must Keeps" to the output file
        f.write('-\n')
        f.write('**The following players should be kept in because they are all up for loot at either Priority or Lottery:**\n')
        # Print Priority players first
        for _, _, playerAndItemRecord in list(filter(lambda entry: entry[0] == "PRIORITY", updatedRaidData[MUST_KEEP_KEY])):
            playerName, itemName = playerAndItemRecord
            f.write('  *PRIORITY*: {} - {}\n'.format(playerName, itemName))
        # Then print Lottery must-keeps. This list is initially aggregated in lottery odds Ascending order due to the insort function
        # used in the perform_evaluation() method, so to print them in descending order (highest on top) we just need to call reversed()
        for _, odds, playerAndItemRecord in reversed(list(filter(lambda entry: entry[0] == "LOTTERY", updatedRaidData[MUST_KEEP_KEY]))):
            playerName, itemName = playerAndItemRecord
            f.write('  LOTTERY: {} - {} ({}% odds)\n'.format(playerName, itemName, odds))

        if updatedRaidData[NUM_SITS_KEY] > 0:
            f.write('-\n')
            f.write('**Potential candidates for being sat (and why):**\n')
            for odds, playerAndItemRecord in updatedRaidData[PROPOSED_SITS_KEY]:
                playerName, itemName = playerAndItemRecord

                if updatedPlayerData[playerName][ROLE_KEY] == "Tank":
                    continue # I don't think we'll ever want to sit Tanks (Also included Healers in this for now)
                elif updatedPlayerData[playerName][ROLE_KEY] == "Healer": ## This logic block us just in case I ever want to re-enable Healer evaluation
                    if itemName == "Has nothing on Lottery":
                        f.write('- **{}** - Is not up for anything on Priority and has nothing on Lottery.\n'.format(playerName))
                    elif itemName == "Can't win any of their Lottery items":
                        f.write('- **{}** - Is not up for anything on Priority and also cannot win any of their desired Lottery items\n'.format(playerName))                            
                    else:
                        f.write('- **{}** - Is not up for anything on Priority and highest Lottery odds are {}% for {}.\n'.format(playerName, odds, itemName))
                    
                    if updatedPlayerData[playerName][PRIO_SECOND_UP_LIST_KEY]:
                        f.write('-    {} is SECOND in line for the following item(s) at Priority: {}\n'.format(playerName, updatedPlayerData[playerName][PRIO_SECOND_UP_LIST_KEY]))  
                    f.write('-    {} is a **Healer**.\n'.format(playerName))                        
                else:
                    if itemName == "Has nothing on Lottery":
                        f.write('- **{}** - Is not immediately up for anything on Priority and has nothing on Lottery\n'.format(playerName))
                    elif itemName == "Can't win any of their Lottery items":
                        f.write('- **{}** - Is not up for anything on Priority and also cannot win any of their desired Lottery items\n'.format(playerName))
                    else:
                        f.write('- **{}** - Is not immediately up for anything on Priority and highest Lottery odds are {}% for {}\n'.format(playerName, odds, itemName))
                    if updatedPlayerData[playerName][PRIO_SECOND_UP_LIST_KEY]:
                        f.write('-    {} is SECOND in line for the following item(s) at Priority: {}\n'.format(playerName, updatedPlayerData[playerName][PRIO_SECOND_UP_LIST_KEY]))

                # Post any additional roster-planning callouts for this player (if any)
                if playerName in SPECIFIC_ROSTER_CALLOUTS:
                    for callout in SPECIFIC_ROSTER_CALLOUTS[playerName]:
                        f.write('-    {} {}.\n'.format(playerName, callout))


if __name__ == "__main__":
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)

    # Load the player_data.yaml file from the all-in-one/ repo
    repoDir = os.path.abspath(os.path.join(scriptDir, os.pardir))
    allInOneGitRepoFilePath = os.path.join(repoDir, 'all-in-one', ALL_IN_ONE_CONFIG_FOLDER_NAME, PLAYER_DATA_FILE_NAME)
    playerYamlDataDict = {}
    with open(allInOneGitRepoFilePath, 'r', encoding='utf-8') as yamlFile:
        playerYamlDataDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

    inputFilePath = os.path.join(scriptDir, INPUT_DATA_FOLDER_NAME, INPUT_DATA_FILE_NAME)
    raidData, playerData = parse_raw_roster_input_and_saturate_dicts(inputFilePath, playerYamlDataDict)

    updatedRaidData, updatedPlayerData = perform_evaluation(raidData, playerData, playerYamlDataDict)

    generate_report_file(scriptDir, updatedRaidData, updatedPlayerData)

    sys.exit(0)


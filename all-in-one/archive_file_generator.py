from datetime import datetime
import os
import re

"""
Given the AddOn data as a dictionary, generate the Lua data tables we desire.
The specific tables we want to have present in the TnTClassic-Archive are:
    - T4_PRIORITY_TRANSACTIONS
    - T4_LOTTERY_TRANSACTIONS
    - T4_OPEN_TRANSACTIONS
    - PLAYER_PRIORITY_REGISTRY
    - PLAYER_LOTTERY_REGISTRY
"""
def generate_archive_lua_file_from_addon_data(addonDataDict, outputDir):
    archiveDataFileName = generate_archive_file_name(addonDataDict)
    with open(os.path.join(outputDir, archiveDataFileName), "w", encoding='utf-8') as f:

        # Output the DKP tables        
        f.write('T4_PRIORITY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T4_PRIORITY_DKP_TABLE'])
        f.write('}\n')

        f.write('T4_LOTTERY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T4_LOTTERY_DKP_TABLE'])
        f.write('}\n')

        f.write('T5_PRIORITY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T5_PRIORITY_DKP_TABLE'])
        f.write('}\n')

        f.write('T5_LOTTERY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T5_LOTTERY_DKP_TABLE'])
        f.write('}\n')

        f.write('T6_PRIORITY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T6_PRIORITY_DKP_TABLE'])
        f.write('}\n')

        f.write('T6_LOTTERY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T6_LOTTERY_DKP_TABLE'])
        f.write('}\n')

        f.write('T6PT5_PRIORITY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T6PT5_PRIORITY_DKP_TABLE'])
        f.write('}\n')

        f.write('T6PT5_LOTTERY_DKP_TABLE = {\n')
        print_dkp_to_file_as_lua_table(f, addonDataDict['T6PT5_LOTTERY_DKP_TABLE'])
        f.write('}\n')

        # Output the Transactions tables
        f.write('T4_PRIORITY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T4_PRIORITY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T4_LOTTERY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T4_LOTTERY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T4_OPEN_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T4_OPEN_TRANSACTIONS'])
        f.write('}\n')

        f.write('T5_PRIORITY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T5_PRIORITY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T5_LOTTERY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T5_LOTTERY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T5_OPEN_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T5_OPEN_TRANSACTIONS'])
        f.write('}\n')

        f.write('T6_PRIORITY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T6_PRIORITY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T6_LOTTERY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T6_LOTTERY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T6_OPEN_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T6_OPEN_TRANSACTIONS'])
        f.write('}\n')

        f.write('T6PT5_PRIORITY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T6PT5_PRIORITY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T6PT5_LOTTERY_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T6PT5_LOTTERY_TRANSACTIONS'])
        f.write('}\n')

        f.write('T6PT5_OPEN_TRANSACTIONS = {\n')
        print_transaction_records_to_file_as_lua_table(f, addonDataDict['T6PT5_OPEN_TRANSACTIONS'])
        f.write('}\n')

        # Output the Priority and Lottery LootConfig/Registries
        f.write('PLAYER_PRIORITY_REGISTRY = {\n')
        print_lootconfig_records_to_file_as_lua_table(f, addonDataDict['PLAYER_PRIORITY_REGISTRY'])
        f.write('}\n')

        f.write('PLAYER_LOTTERY_REGISTRY = {\n')
        print_lootconfig_records_to_file_as_lua_table(f, addonDataDict['PLAYER_LOTTERY_REGISTRY'])
        f.write('}\n')

    return archiveDataFileName

"""
Transforms the given LootConfig Dictionary into Lua table format, printing each entry to
the provided filestream.
"""
def print_lootconfig_records_to_file_as_lua_table(outputFile, lootConfigDict):
    for itemID in lootConfigDict:
        outputFile.write("	[{}] = {{\n".format(int(itemID)))

        for player in lootConfigDict[itemID].keys():
            outputFile.write('		["{}"] = {},\n'.format(player, lootConfigDict[itemID][player]))

        outputFile.write("	},\n")

'''
Transforms the given dkpDict into Lua table format, printing each entry to
the provided filestream.
'''
def print_dkp_to_file_as_lua_table(outputFile, dkpDict):
    for player in dkpDict:
        outputFile.write('   ["{}"] = {},\n'.format(player,dkpDict[player]))

'''
Transforms the given Transactions Dictionary into Lua table format, printing each entry to
the provided filestream.
'''
def print_transaction_records_to_file_as_lua_table(outputFile, transactionsDict):
    recordNum = 1
    for transactionRecord in transactionsDict:
        outputFile.write('   {\n')
        outputFile.write('      "{}", -- [1]\n'.format(transactionRecord['Recipient']))
        outputFile.write('      "{}", -- [2]\n'.format(transactionRecord['Issuer']))
        outputFile.write('      "{}", -- [3]\n'.format(transactionRecord['Message']))
        outputFile.write('      {}, -- [4]\n'.format(transactionRecord['DKPBefore']))
        outputFile.write('      {}, -- [5]\n'.format(transactionRecord['DKPAfter']))
        outputFile.write('      "{}", -- [6]\n'.format(transactionRecord['ItemLink']))
        outputFile.write('      "{}", -- [7]\n'.format(transactionRecord['ID']))
        outputFile.write('      "{}", -- [8]\n'.format(datetime.strftime(transactionRecord['Timestamp'], "%a %b %d %H:%M:%S %Y")))
        outputFile.write('   }}, -- [{}]\n'.format(recordNum))

        recordNum += 1

"""
We name our AddOn data files in the format "2021_08_08_Mag+Gruul.lua" when we
upload them to the TnTClassic-Archive repository. This logic auto-generates
that name based on the AddOn output data
"""
def generate_archive_file_name(addonDataDict):
    GRUULS_LAIR_BOSSES = ["Dragonkiller", "Maulgar"]
    SSC_BOSSES = ["Unstable", "Below", "Blind", "Karathress", "Tidewalker", "Vashj"]
    TK_BOSSES = ["Al'ar", "Reaver", "Solarian", "Sunstrider"]

    transactionsTables = [
        'T4_PRIORITY_TRANSACTIONS', 'T4_LOTTERY_TRANSACTIONS', 'T4_OPEN_TRANSACTIONS', 
        'T5_PRIORITY_TRANSACTIONS', 'T5_LOTTERY_TRANSACTIONS', 'T5_OPEN_TRANSACTIONS', 
        'T6_PRIORITY_TRANSACTIONS', 'T6_LOTTERY_TRANSACTIONS', 'T6_OPEN_TRANSACTIONS', 
        'T6PT5_PRIORITY_TRANSACTIONS', 'T6PT5_LOTTERY_TRANSACTIONS', 'T6PT5_OPEN_TRANSACTIONS'
    ]
    
    # Generate a filename of the format: "2021_08_08_Mag+Gruul.lua"
    mostRecentTransactionTimestamp = datetime(2001, 1, 1)
    raidsPresentInTransactions = set()
    
    # Iterate over ALL transactions to try to determine the most recent
    # transaction as well as which boss kills were present in them
    isDecay = False
    for transactionsTable in transactionsTables:
        for transactionRecord in addonDataDict[transactionsTable]:
            timestamp = transactionRecord['Timestamp']
            if timestamp > mostRecentTransactionTimestamp:
                mostRecentTransactionTimestamp = timestamp

            message = transactionRecord['Message']

            # Weekly decays are done on their own accord, they aren't tacked onto the end of raid nights. If a single weekly
            # decay message is apparent in the log, that means that the entire log is nothing but decay messages
            if re.search("All DKP Tables decayed by", message) is not None:
                isDecay = True
                break
            elif re.search(" [A-Z]*[a-z]+$", message) is not None:
                bossName = re.search(" [A-Z]*[a-z]+$", message).group()[1:]
                if bossName == "Magtheridon":
                    raidsPresentInTransactions.add('Mag')
                elif bossName in GRUULS_LAIR_BOSSES:
                    raidsPresentInTransactions.add('Gruul')
                elif bossName in SSC_BOSSES:
                    raidsPresentInTransactions.add('SSC')
                elif bossName in TK_BOSSES:
                    raidsPresentInTransactions.add('TK')

    # Convert mostRecentTransactionTimestamp to proper string format: "2020_02_04"
    filenameDateSegment = mostRecentTransactionTimestamp.strftime("%Y_%m_%d")

    filenameContentSegment = None
    if isDecay:
        filenameContentSegment = "Weekly_Decay"
    else:
        # Generate the Raid+Concat+String. (This is where we set the order of the file name)
        raidTiersInOrder = []
        if 'Mag' in raidsPresentInTransactions:
            raidTiersInOrder.append('Mag')
        if 'Gruul' in raidsPresentInTransactions:
            raidTiersInOrder.append('Gruul')
        if 'SSC' in raidsPresentInTransactions:
            raidTiersInOrder.append('SSC')
        if 'TK' in raidsPresentInTransactions:
            raidTiersInOrder.append('TK')
        filenameContentSegment = '+'.join(raidTiersInOrder)

    # Take the previous two values and produce the archive file name
    return "{}_{}.lua".format(filenameDateSegment, filenameContentSegment)

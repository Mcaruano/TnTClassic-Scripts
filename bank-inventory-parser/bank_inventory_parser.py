# coding=utf-8

# This script takes Transaction Data from TnTBankTransactionMonitor and "replays" it to construct
# a dictionary of what the Guild Bank inventory *should* be according to this data. It also stores each
# of the transactions into a separate dictionary for hosting on the website


from datetime import datetime
import math
import os
import re
import sys


BANK_DATA_FOLDER_NAME = "bank_data"
TRANSACTION_DATA_FILE_NAME = "TnTBankTransactionMonitor.lua"
BANK_SNAPSHOT_FILE_NAME = "TnTCharacterBankSnapshotter.lua"

OUTPUT_DATA_FOLDER_NAME = "gen"
AUDIT_RESULTS_FILE_NAME = "tnt_bank_inventory.csv"

ITEM_ID_TO_STRING_NAME_MAP = {
    15410: "Scale of Onyxia",
    7078: "Essence of Fire",
    11382: "Blood of the Mountain",
    17011: "Lava Core",
    15138: "Onyxia Scale Cloak",
    8170: "Rugged Leather",
    7068: "Elemental Fire",
    12359: "Thorium Bar",
    11370: "Dark Iron Ore",
    7067: "Elemental Earth",
    7076: "Essence of Earth",
    13457: "Greater Fire Protection Potion",
    17203: "Sulfuron Ingot",
    7191: "Fused Wiring",
    17010: "Fiery Core",
    17012: "Core Leather",
    11979: "Peridot Circle of Nature Resistance",
    11371: "Dark Iron Bar",
    0: "Gold",
}

"""
Parse the data from the TnTBankTransactionMonitor AddOn into a Dictionary as such:
{
    {'InboundTransactions':
        [
            {
                'TransactionID': 06324804450366025314,
                'Timestamp': datetime.datetime(2019, 10, 22, 18, 56, 22),
                'Sender': 'Akaran',
                'ItemID': 2678,
                'Quantity': 3
            },
            ...
        ]
    },
    {'OutboundTransactions':
        [
            {
                'TransactionID': 06324804450366025314,
                'Timestamp': datetime.datetime(2019, 10, 22, 18, 56, 22),
                'Recipient': 'Akaran',
                'ItemID': 2678,
                'Quantity': 3
            },
            ...
        ]
    }
}
"""
def parse_transaction_data_to_dict(transactionDataFilePath):
    f = open(transactionDataFilePath, "r")
    lines = f.readlines()
    f.close()

    bankTransactionDataDict = {}
    bankTransactionDataDict['InboundTransactions'] = []
    bankTransactionDataDict['OutboundTransactions'] = []
    currentKey = 'InboundTransactions'
    for line in lines:
        
        if re.search("InboundTransactions = {", line) is not None:
            currentKey = 'InboundTransactions'
            continue

        if re.search("OutboundTransactions = {", line) is not None:
            currentKey = 'OutboundTransactions'
            continue

        # InboundTransactions = {
        #     "06324804450366025314,Mon Sep 23 00:55:48 2019,Akaran,2678,3", -- [1]
        #     "04112529590112784971,Mon Sep 23 00:55:49 2019,Akaran,2320,1", -- [2]
        #     "18134585131599854387,Mon Sep 23 00:55:49 2019,Akaran,2692,1", -- [3]
        #     ....
        #
        # This pattern matches the "06324804450366025314,Mon Sep 23 00:55:48 2019,Akaran,2678,3"
        # value, and trims off the leading " and trailing ",
        if re.search("\".*\",", line) is not None:
            record = re.search("\".*\",", line).group()[1:-2]

            # Split the record by "," and load it into a Dict
            values = record.split(',')
            recordDict = {}
            recordDict['TransactionID'] = int(values[0])
            recordDict['Timestamp'] = datetime.strptime(values[1], '%a %b %d %H:%M:%S %Y')
            senderOrRecipient = 'Sender' if currentKey == 'InboundTransactions' else 'Recipient'
            recordDict[senderOrRecipient] = values[2]
            recordDict['ItemID'] = int(values[3])
            recordDict['Quantity'] = int(values[4])

            # Insert the transaction into the appropriate key
            bankTransactionDataDict[currentKey].append(recordDict)

    return bankTransactionDataDict

"""
Parse the Bank snapshot from the file and read it into a Dict of the following format:
{
    13040: 1,
    17011: 19,
    ...
    14504: 1,
    0: 4307920
}
where the Key is the ItemID, and the value is the Quantity.
NOTE: The record with ItemID of 0 represents the money (in Copper) on the character
"""
def parse_bank_snapshot_to_dict(bankSnapshotFilePath):
    f = open(bankSnapshotFilePath, "r")
    lines = f.readlines()
    f.close()
    
    bankSnapshotDataDict = {}
    for line in lines:

        # The BankContent records are in the following format:
        #
        # BankContents = {
        #   "Tntbank,13040,1", -- [1]
        #   "Tntbank,17011,19", -- [2]
        #     .....
        #   "Tntbank,14504,1", -- [27]
        #   "Tntbank,0,4307920", -- [28]
        # }
        #
        # This pattern matches the "Tntbank,13040,1" value, and trims off the leading " and trailing ",
        if re.search("\".*\",", line) is not None:
            record = re.search("\".*\",", line).group()[1:-2]
        
            # Split the record by "," and load it into a Dict
            values = record.split(',')
            itemID = int(values[1])
            quantity = int(values[2])

            # Insert that dict into the list
            bankSnapshotDataDict[itemID] = quantity

    return bankSnapshotDataDict


"""
STUB: Override this to do something meaningful with the transaction data
"""
def write_transaction_history_to_db_table(transactionDataDict):
    return True

"""
This method simply takes the "true" inventory data (doesn't try to reconstruct it
by replaying the Transactions) and outputs it to a CSV so that we can temporarily
host in on Google Sheets for the guild members to view.
"""
def write_current_inventory_to_csv(outputFilePath, currentInventoryDict, transactionDataDict):

    # Since Transactions are recorded in chronological order and parsed in that same order, the last Transactions from
    # each of the Inbound and Outbound lists will be the most recent ones. I simply compare the last of each to determine
    # the timestamp of the most recent bank transaction present in this data set.
    latestInboundTransactionDatetime = transactionDataDict['InboundTransactions'][-1]['Timestamp']
    latestOutboundTransactionDatetime = transactionDataDict['OutboundTransactions'][-1]['Timestamp']
    latestTransactionDatetime = latestInboundTransactionDatetime if latestInboundTransactionDatetime >= latestOutboundTransactionDatetime else latestOutboundTransactionDatetime

    with open(outputFilePath, 'w') as f:
        f.write("TnT Guild Bank Inventory as of {}\n".format(latestTransactionDatetime.strftime("%m/%d/%Y @ %I:%M%p")))
        f.write("ITEM,QUANTITY,LINK\n") # Column Headers
        for itemID,quantity in sorted(currentInventoryDict.items(), key=lambda item: ITEM_ID_TO_STRING_NAME_MAP[item[0]]):
            if itemID == 0:
                f.write("{},{}\n".format(ITEM_ID_TO_STRING_NAME_MAP[itemID], math.floor(quantity/10000)))
            else:
                f.write("{},{},https://classic.wowhead.com/item={}\n".format(ITEM_ID_TO_STRING_NAME_MAP[itemID], quantity, itemID))

    return True


if __name__ == "__main__":
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)

    transactionDataFilePath = os.path.join(scriptDir, BANK_DATA_FOLDER_NAME, TRANSACTION_DATA_FILE_NAME)
    transactionDataDict = parse_transaction_data_to_dict(transactionDataFilePath)

    bankSnapshotFilePath = os.path.join(scriptDir, BANK_DATA_FOLDER_NAME, BANK_SNAPSHOT_FILE_NAME)
    bankSnapshotDict = parse_bank_snapshot_to_dict(bankSnapshotFilePath)

    # Generate the output directory if it doesn't exist
    outputFileDirectory = os.path.join(scriptDir, OUTPUT_DATA_FOLDER_NAME)
    if not os.path.exists(outputFileDirectory):
        os.makedirs(outputFileDirectory)
    outputFilePath = os.path.join(outputFileDirectory, AUDIT_RESULTS_FILE_NAME)

    write_transaction_history_to_db_table(transactionDataDict)

    write_current_inventory_to_csv(outputFilePath, bankSnapshotDict, transactionDataDict)

    sys.exit(0)
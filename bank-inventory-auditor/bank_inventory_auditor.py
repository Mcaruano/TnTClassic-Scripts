# coding=utf-8

# To manage our Guild Bank inventory and maintain a high integrity, we have two AddOns which record
# the inventory data:
#   1. TnTBankTransactionMonitor listens to all incoming and outgoing item transactions,
#      whether it be by mail or by trade, and records them.
#   2. TnTCharacterBankSnapshotter simply takes a snapshot of all items in the bank alt's
#      bags and bank and writes it to a file
#
# This script takes Transaction Data from TnTBankTransactionMonitor and "replay"s it, to construct
# a view of what the Guild Bank inventory *should* be according to this data. It then cross-references
# that with what the Guild Bank inventory *actually is* as output by the TnTCharacterBankSnapshotter.
#
# If no discrepancies are found, it prints to the terminal letting the user know. If discrepancies were
# found, a full report of the discrepancies is output to output/bank_audit_results.txt, broken down by
# ItemID, together with the Transaction records from that ItemID


from datetime import datetime
import os
import re
import sys


BANK_DATA_FOLDER_NAME = "bank_data_files"
TRANSACTION_DATA_FILE_NAME = "TnTBankTransactionMonitor.lua"
BANK_SNAPSHOT_FILE_NAME = "TnTCharacterBankSnapshotter.lua"

OUTPUT_DATA_FOLDER_NAME = "output"
AUDIT_RESULTS_FILE_NAME = "bank_audit_results.txt"




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
Given the raw data from the TnTBankTransactionMonitor, build a record of the
guild bank inventory by "replaying" the Inbound and Outbound Transactions.
"""
def build_inventory_from_transactions(transactionDataDict):
    inventory = {}

    # "Add" inbound transactions to the inventory
    for record in transactionDataDict['InboundTransactions']:
        itemID = record['ItemID']
        if itemID not in inventory:
            inventory[itemID] = record['Quantity']
        else:
            inventory[itemID] = inventory[itemID] + record['Quantity']

    # "Subtract" outbound transactions from the inventory. We allow negative quantities here.
    for record in transactionDataDict['OutboundTransactions']:
        itemID = record['ItemID']
        if itemID not in inventory:
            inventory[itemID] = -record['Quantity']
        else:
            inventory[itemID] = inventory[itemID] - record['Quantity']

    return inventory


"""
The bulk of the work is executed here. The bank's inventory as recorded by the Transactions Data
is compared to the bank's inventory as recorded by the Snapshotter to detect any discrepancies.
"""
def perform_audit_and_output_to_file(transactionDataDict, bankSnapshotDict, outputFilePath):
    discrepanciesDetected = False
    transactionsInventoryDict = build_inventory_from_transactions(transactionDataDict)

    itemIDsInTransactions = set()
    for itemID in transactionsInventoryDict:
        if transactionsInventoryDict[itemID] != 0:
            itemIDsInTransactions.add(itemID)

    itemIDsInSnapshot = set()
    for itemID in bankSnapshotDict:
        if bankSnapshotDict[itemID] != 0:
            itemIDsInSnapshot.add(itemID)

    itemIDsOnlyInTransactions = itemIDsInTransactions.difference(itemIDsInSnapshot)
    itemIDsOnlyInSnapshot = itemIDsInSnapshot.difference(itemIDsInTransactions)

    with open(outputFilePath, "w") as f:
        if len(itemIDsOnlyInTransactions) > 0 or len(itemIDsOnlyInSnapshot) > 0:
            f.write("================================================================\n")
            f.write("===================== Missing Items Report =====================\n")
            f.write("================================================================\n")
        if len(itemIDsOnlyInTransactions) > 0:
            discrepanciesDetected = True
            f.write("\n==== Items in Transactions Log but NOT in Snapshot ====")
            f.write("\n-------------------------------------------------------")
            for itemID in itemIDsOnlyInTransactions:
                f.write("\n * ItemID: {}, Qty: {}".format(itemID, transactionsInventoryDict[itemID]))

            f.write("\n\n================ Transaction Tracelog ================")
            f.write("\n------------------------------------------------------")
            for itemID in itemIDsOnlyInTransactions:
                f.write("\n==== Transaction History for ItemID: {} ====\n".format(itemID))
                # Print the Inbound Transaction records for this ItemID
                headerWasPrinted = False
                for record in transactionDataDict['InboundTransactions']:
                    if record['ItemID'] == itemID:
                        if not headerWasPrinted:
                            f.write("  >>> Inbound >>>\n")
                            headerWasPrinted = True
                        f.write("    DATE: {}, FROM: {}, QTY: {}     ID: [{}]\n".format(datetime.strftime(record['Timestamp'], '%a %b %d %H:%M:%S %Y'), record['Sender'], record['Quantity'], record['TransactionID']))

                # Print the Outbound Transaction records for this ItemID
                headerWasPrinted = False
                for record in transactionDataDict['OutboundTransactions']:
                    if record['ItemID'] == itemID:
                        if not headerWasPrinted:
                            f.write("  <<< Outbound <<<\n")
                            headerWasPrinted = True
                        f.write("    DATE: {}, TO: {}, QTY: {}     ID: [{}]\n".format(datetime.strftime(record['Timestamp'], '%a %b %d %H:%M:%S %Y'), record['Recipient'], record['Quantity'], record['TransactionID']))

        if len(itemIDsOnlyInSnapshot) > 0:
            discrepanciesDetected = True
            f.write("\n==== Items From Snapshot Log That Weren't in the Transactions ====")
            for itemID in itemIDsOnlyInSnapshot:
                f.write("{}: {}\n".format(itemID, bankSnapshotDict[itemID]))

        # Since the outliers have been handled, we now just need to compare the ItemIDs which
        # both data sets share and confirm that their Quantities match up.
        headerWasPrinted = False
        for itemID in itemIDsInTransactions.intersection(itemIDsInSnapshot):
            if bankSnapshotDict[itemID] != transactionsInventoryDict[itemID]:
                discrepanciesDetected = True
                if not headerWasPrinted:
                    f.write("\n\n================================================================\n")
                    f.write("================== Quantity Discrepancy Report =================\n")
                    f.write("================================================================")
                    headerWasPrinted = True
                f.write("\nDiscrepancy detected for ItemID: {}".format(itemID))
                f.write("\n  Snapshot Qty: {}".format(bankSnapshotDict[itemID]))
                f.write("\n  Transactions Qty: {}".format(transactionsInventoryDict[itemID]))
                if bankSnapshotDict[itemID] - transactionsInventoryDict[itemID] > 0:
                    f.write("\n  DIFFERENCE: Bank has {} MORE than it should have\n".format(abs(bankSnapshotDict[itemID] - transactionsInventoryDict[itemID])))
                else:
                    f.write("\n  DIFFERENCE: Bank has {} LESS than it should have\n".format(abs(bankSnapshotDict[itemID] - transactionsInventoryDict[itemID])))

                # Print the Inbound Transaction records for this ItemID
                headerWasPrinted = False
                for record in transactionDataDict['InboundTransactions']:
                    if record['ItemID'] == itemID:
                        if not headerWasPrinted:
                            f.write("  >>> Inbound >>>\n")
                            headerWasPrinted = True
                        f.write("    DATE: {}, FROM: {}, QTY: {}     ID: [{}]\n".format(datetime.strftime(record['Timestamp'], '%a %b %d %H:%M:%S %Y'), record['Sender'], record['Quantity'], record['TransactionID']))

                # Print the Outbound Transaction records for this ItemID
                headerWasPrinted = False
                for record in transactionDataDict['OutboundTransactions']:
                    if record['ItemID'] == itemID:
                        if not headerWasPrinted:
                            f.write("  <<< Outbound <<<\n")
                            headerWasPrinted = True
                        f.write("    DATE: {}, TO: {}, QTY: {}     ID: [{}]\n".format(datetime.strftime(record['Timestamp'], '%a %b %d %H:%M:%S %Y'), record['Recipient'], record['Quantity'], record['TransactionID']))

    return discrepanciesDetected


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

    discrepancyFound = perform_audit_and_output_to_file(transactionDataDict, bankSnapshotDict, outputFilePath)

    if discrepancyFound:
        print("BANK DATA DISCREPANCY FOUND. Check {} for details".format(outputFilePath))
    else:
        print("No discrepancies found in the bank data!")

    sys.exit(0)
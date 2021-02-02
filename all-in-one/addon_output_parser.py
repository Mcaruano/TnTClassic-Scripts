from datetime import datetime
import re

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

      'LOTTERY_TRANSACTIONS':
        [
          {'DKPAfter': 2450,
           'DKPBefore': 2425,
           'ID': 3551598920298475579,
           'Issuer': 'Nocjr',
           'ItemLink': '',
           'Message': '[DKP +25]: on time',
           'Recipient': 'Iopo',
           'Timestamp': datetime.datetime(2019, 10, 22, 18, 56, 22)},
          
            ...

          {'DKPAfter': 900,
           'DKPBefore': 1900,
           'ID': 14231057000375578302L,
           'Issuer': 'Nocjr',
           'ItemLink': '',
           'Message': '[Lottery DKP -1000]: Head of Onyxia (ItemID: 18423)',
           'Recipient': 'Nocjr',
           'Timestamp': datetime.datetime(2019, 10, 22, 18, 56, 22)}
        ],

      'PLAYER_LOTTERY_REGISTRY':
        {
          '16795': {'Mlg': 1,
                   'Thejudge': 1,
                   'Tongsta': 1},
          '16797': {'Grigg': 1},

          ...

          '19147': {'Crimfall': 1,
                   'Gillaen': 1,
                   'Mlg': 1,
                   'Tongsta': 1,
                   'Volkazar': 1}
        },

      'ITEMS_RECEIVED':
        {
          'PRIORITY': {'Mlg': set(17017),
                   'Thejudge': set(18082, 19090),
                   'Tongsta': set(16820)},
          'LOTTERY': {'Grigg': set(17017)},
        },
    }
NOTE: PLAYER_LOTTERY_REGISTRY and PLAYER_PRIORITY_REGISTRY use ItemID as a STRING for the key. This
would have to be parsed as an int before entry into our back-end
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

            # For T2.5, I have variable names which don't follow the standard LUA variable pattern. This prepends
            # a (T2)* onto the front of the pattern to capture T2PT5_* variable names.
            variableName = re.search("(T2)*[A-Z]+[0-9]*(_[A-Z]+)* = ", line).group()[:-3]
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
    if len(dictKeyStack) <= 0: return
    currentKey = dictKeyStack[-1]

    # Example structure of a _REGISTRY entry:
    # PLAYER_PRIORITY_REGISTRY = {
    #     [16908] = {
    #         ["Nekz"] = 1,
    #         ["Nocjr"] = 1,
    #         ["Haast"] = 1,
    #     },
    # }
    if re.search("^[0-9]+?", currentKey) is not None:
        # Parse the player name. Due to dumbasses using special characters in their names,
        # we have to match the entire "UserName" block and trim off the quotes
        playerName = re.search("\".*\"", data_record).group()[1:-1]
        quantity = int(re.search("[0-9]+", data_record).group())
        dictForItemID = dataDict[dictKeyStack[-2]][dictKeyStack[-1]]
        dictForItemID[playerName] = quantity
        # print("Playername in item registry: {}. Quantity: {}. Relevant Dict: {}".format(playerName, quantity, dictForItemID))

    # Example structure of a _DKP_TABLE entry:
    # PRIORITY_DKP_TABLE = {
    #     ["Noxyqt"] = 1600,
    # }
    elif currentKey.endswith("_DKP_TABLE"):
        # Parse the player name. Due to dumbasses using special characters in their names,
        # we have to match the entire "UserName" block and trim off the quotes
        playerName = re.search("\".*\"", data_record).group()[1:-1]
        dkp = float(re.search("-?[0-9]+(\.[0-9]+)?", data_record).group())
        dictForItemID = dataDict[dictKeyStack[-1]]
        dictForItemID[playerName] = dkp

    # Example structure of a _TRANSACTIONS entry (note the [i] indices):
    # PRIORITY_TRANSACTIONS = {
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
    elif currentKey.endswith("_TRANSACTIONS"):
        # Match the opening bracket of a transaction record and skip it
        if re.search("{", data_record) is not None:
            return
        # Match the closing bracket of a transaction record and skip it
        if re.search("},", data_record) is not None:
            return
        # Parse the index that trails the end of each field of the transaction record
        if re.search("\[[0-9]+\]", data_record) is None:
            print("Index was not found for data_record: {}".format(data_record))

        index = int(re.search("\[[0-9]+\]", data_record).group()[1:-1])

        value = None
        if re.search("\".*\",", data_record) is not None:
            # Parse the actual value by matching '"Iopo",' and trimming off the leading " and trailing ",
            value = re.search("\".*\",", data_record).group()[1:-2]
        else:
            # Parse the actual value by matching '-1425, --' and trimming off the trailing ", --",
            value = re.search("-?[0-9]+.?[0-9]*, --", data_record).group()[:-4]

        # If this is the first element of a new transaction record, create a new dict for it in the transactions list
        if index == 1:
            dataDict[currentKey].append({})

        currentTransactionRecord = dataDict[currentKey][-1]        

        # Recipient
        if index == 1:
            currentTransactionRecord['Recipient'] = value

        # Issuer (the person who awarded the DKP)
        elif index == 2:
            currentTransactionRecord['Issuer'] = value

        # Message
        elif index == 3:
            currentTransactionRecord['Message'] = value
            dataDict['ITEMS_RECEIVED'] = parse_message_and_record_item_received(dataDict['ITEMS_RECEIVED'], currentTransactionRecord['Recipient'], value)
            isLootRecord, itemID, lootMode = parse_loot_related_metadata(value)
            currentTransactionRecord['IsLootRecord'] = isLootRecord
            currentTransactionRecord['ItemID'] = itemID
            currentTransactionRecord['LootMode'] = lootMode

        # DKP Before
        elif index == 4:
            currentTransactionRecord['DKPBefore'] = float(value)

        # DKP After
        elif index == 5:
            currentTransactionRecord['DKPAfter'] = float(value)

        # Itemlink. Currently unused.
        elif index == 6:
            if value != "":
                currentTransactionRecord['ItemLink'] = value
                print("Parsed an itemlink: {}".format(value))
            else:
                currentTransactionRecord['ItemLink'] = ""

        # Transaction ID
        elif index == 7:
            # This is edge-case handling for some inconsistent logic in the AddOn where I accidentally added two
            # "" fields into the Transaction record at indeces 7 and 8.
            # TODO: Remove this logic after merging the first set of data, as this won't occur again
            if value != "":
                currentTransactionRecord['ID'] = int(value)

        # Transaction Timestamp of the format: "Tue Oct 22 18:56:22 2019"
        elif index == 8:
            # This is edge-case handling for some inconsistent logic in the AddOn where I accidentally added two
            # "" fields into the Transaction record at indeces 7 and 8.
            # TODO: Remove this logic after merging the first set of data, as this won't occur again
            if value != "":
                currentTransactionRecord['Timestamp'] = datetime.strptime(value, '%a %b %d %H:%M:%S %Y')

        # This is edge-case handling for some inconsistent logic in the AddOn where I accidentally added two
        # "" fields into the Transaction record at indeces 7 and 8. Such rows have ID and Timestamp shifted
        # down by two, where 9 == ID and 10 == Timestamp. An example is a record like so:
        #
        # {
        #     "Searus", -- [1]
        #     "Nocjr", -- [2]
        #     "[Lottery DKP -1000]: Nightslayer Gloves - 16826", -- [3]
        #     1775, -- [4]
        #     775, -- [5]
        #     "", -- [6]
        #     "", -- [7]
        #     "", -- [8]
        #     "14183475120346263235", -- [9]
        #     "Tue Oct 22 19:38:41 2019", -- [10]
        # }, -- [105]
        #
        # TODO: Remove this logic after merging the first set of data, as this won't occur again
        elif index == 9:
            currentTransactionRecord['ID'] = int(value)
        elif index == 10:
            currentTransactionRecord['Timestamp'] = datetime.strptime(value, '%a %b %d %H:%M:%S %Y')
        

"""
The AddOn output structures messages in a consistent way. When an item is distributed via the AddOn,
the "message" is structured as follows: "[Priority DKP -1000]: Staff of Dominance (ItemID: 18842)"
This method simply takes the message, determines if it was an item distribution, and records data
about it in the dictionary.

As it stands, this is the only way we can discertain what items were received during a raid, which means
this is the only way we can hope to merge the output of two AddOn output files
"""                
def parse_message_and_record_item_received(itemsReceivedSubDict, recipient, message):
    # This pattern matches keys of the format "(ItemID: 19147)", which represents a loot-distribution transaction
    if re.search("\(ItemID: [0-9]+\)", message) is not None:
        itemID = re.search("\(ItemID: [0-9]+\)", message).group()[9:-1]
        mode = "PRIORITY" if re.search("Priority", message) is not None else "LOTTERY"
        if recipient not in itemsReceivedSubDict[mode]:
            itemsReceivedSubDict[mode][recipient] = set()
        itemsReceivedSubDict[mode][recipient].add(itemID)
    return itemsReceivedSubDict


def parse_loot_related_metadata(message):
    isLootRecord = False
    itemID = None
    lootMode = None

    # This pattern matches keys of the format "(ItemID: 19147)", which represents a loot-distribution transaction
    if re.search("\(ItemID: [0-9]+\)", message) is not None:
        itemID = re.search("\(ItemID: [0-9]+\)", message).group()[9:-1]
        lootMode = "PRIORITY" if re.search("Priority", message) is not None else "LOTTERY"
        isLootRecord = True

    # Sometimes a manual transaction must be entered which does NOT adhere to the precise structure of "(ItemID: <itemID>)"
    # in the message body. However, these manual transactions can still be detected if the transaction was -500, -1000, -2000,
    # -3000, or -4000 (aka the cost of an item). In this case, we just want to print this out to the terminal to coax me into
    # correcting the record so it adheres to the desired syntax
    elif re.search("-[0-9]+]:", message) is not None:
        dkpCharge = int(re.search("-[0-9]+]:", message).group()[1:-2])
        if dkpCharge % 500 == 0:
            print("\nFOUND RECORD THAT MIGHT BE LOOT RECORD: {}".format(message))
            lootMode = "PRIORITY" if re.search("Priority", message) is not None else "LOTTERY"

    return isLootRecord, itemID, lootMode

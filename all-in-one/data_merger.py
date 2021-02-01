"""
Given that two players started ith the same data, merge input from one INTO the other - hence the "input" and "master" nomenclature.
The way the data is merged is by identifying which Transactions occurred in the Input data set but NOT
the Master data set, and then walking through those transactions to "replay" the events, resulting in
a merged DKP data set.
"""
def merge_addon_data(masterDataDict, inputDataDict):
    mergedDataDict = {}

    mergedDataDict = merge_t1_data(mergedDataDict, masterDataDict, inputDataDict)

    mergedDataDict = merge_t2_data(mergedDataDict, masterDataDict, inputDataDict)

    # Create a Set of the 'ID's from each of the masterDataDict and inputDataDict 'OPEN_TRANSACTIONS' lists
    # Use Set operations to identify which Transactions are present in the inputDataDict but NOT the masterDataDict
    masterOpenTransactionIDSet = set()
    for record in masterDataDict['OPEN_TRANSACTIONS']:
        if record['ID'] not in masterOpenTransactionIDSet:
            masterOpenTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in masterDataDict. ID: {}".format(record['ID']))
    inputOpenTransactionIDSet = set()
    for record in inputDataDict['OPEN_TRANSACTIONS']:
        if record['ID'] not in inputOpenTransactionIDSet:
            inputOpenTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in inputDataDict. ID: {}".format(record['ID']))

    # Generate merged Open Transaction data
    mergedDataDict['OPEN_TRANSACTIONS'] = masterDataDict['OPEN_TRANSACTIONS']
    openIDsUniqueToInputDataDict = inputOpenTransactionIDSet.difference(masterOpenTransactionIDSet)
    for transactionID in openIDsUniqueToInputDataDict:
        for record in inputDataDict['OPEN_TRANSACTIONS']:
            if record['ID'] == transactionID:
                # There is no DKP data to carry over here, we simply copy the record
                mergedDataDict['OPEN_TRANSACTIONS'].append(record)
                break

    # For each obtained Priority item in the masterDataDict, remove it from the above input set if it exists.
    # The resulting set will be those items obtained ONLY in the input data's raid
    inputObtainedPriorityItemsDict = inputDataDict['ITEMS_RECEIVED']['PRIORITY']
    for recipient in masterDataDict['ITEMS_RECEIVED']['PRIORITY']:
        if recipient in inputObtainedPriorityItemsDict:
            for itemID in masterDataDict['ITEMS_RECEIVED']['PRIORITY'][recipient]:
                if itemID in inputObtainedPriorityItemsDict[recipient]:
                    inputObtainedPriorityItemsDict[recipient].remove(itemID)

    # Iterate over the remaining records in the input data to remove them from the final 'PLAYER_PRIORITY_REGISTRY' LUA Table data.
    # This loop is extremely inefficient but I don't care.
    mergedDataDict['PLAYER_PRIORITY_REGISTRY'] = masterDataDict['PLAYER_PRIORITY_REGISTRY']
    for recipient in inputObtainedPriorityItemsDict:
        for itemID in inputObtainedPriorityItemsDict[recipient]:
            if str(itemID) in mergedDataDict['PLAYER_PRIORITY_REGISTRY']:
                if recipient in mergedDataDict['PLAYER_PRIORITY_REGISTRY'][str(itemID)]:
                    if mergedDataDict['PLAYER_PRIORITY_REGISTRY'][str(itemID)][recipient] > 1:
                        mergedDataDict['PLAYER_PRIORITY_REGISTRY'][str(itemID)][recipient] = mergedDataDict['PLAYER_PRIORITY_REGISTRY'][str(itemID)][recipient] - 1
                    else:
                        del mergedDataDict['PLAYER_PRIORITY_REGISTRY'][str(itemID)][recipient]

    # For each obtained Lottery item in the masterDataDict, remove it from the above input set if it exists.
    # The resulting set will be those items obtained ONLY in the input data's raid
    inputObtainedLotteryItemsDict = inputDataDict['ITEMS_RECEIVED']['LOTTERY']
    for recipient in masterDataDict['ITEMS_RECEIVED']['LOTTERY']:
        if recipient in inputObtainedLotteryItemsDict:
            for itemID in masterDataDict['ITEMS_RECEIVED']['LOTTERY'][recipient]:
                if itemID in inputObtainedLotteryItemsDict[recipient]:
                    inputObtainedLotteryItemsDict[recipient].remove(itemID)


    # Iterate over the remaining records in the input data to remove them from the final 'PLAYER_LOTTERY_REGISTRY' LUA Table data.
    # This loop is extremely inefficient but I don't care.
    mergedDataDict['PLAYER_LOTTERY_REGISTRY'] = masterDataDict['PLAYER_LOTTERY_REGISTRY']
    for recipient in inputObtainedLotteryItemsDict:
        for itemID in inputObtainedLotteryItemsDict[recipient]:
            if str(itemID) in mergedDataDict['PLAYER_LOTTERY_REGISTRY']:
                if recipient in mergedDataDict['PLAYER_LOTTERY_REGISTRY'][str(itemID)]:
                    if mergedDataDict['PLAYER_LOTTERY_REGISTRY'][str(itemID)][recipient] > 1:
                        mergedDataDict['PLAYER_LOTTERY_REGISTRY'][str(itemID)][recipient] = mergedDataDict['PLAYER_LOTTERY_REGISTRY'][str(itemID)][recipient] - 1
                    else:
                        del mergedDataDict['PLAYER_LOTTERY_REGISTRY'][str(itemID)][recipient]

    return mergedDataDict

def merge_t1_data(mergedDataDict, masterDataDict, inputDataDict):
    # Create a Set of the 'ID's from each of the masterDataDict and inputDataDict 'PRIORITY_TRANSACTIONS' lists
    # Use Set operations to identify which Transactions are present in the inputDataDict but NOT the masterDataDict
    masterPriorityTransactionIDSet = set()
    for record in masterDataDict['T1_PRIORITY_TRANSACTIONS']:
        if record['ID'] not in masterPriorityTransactionIDSet:
            masterPriorityTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in masterDataDict. ID: {}".format(record['ID']))
    inputPriorityTransactionIDSet = set()
    for record in inputDataDict['T1_PRIORITY_TRANSACTIONS']:
        if record['ID'] not in inputPriorityTransactionIDSet:
            inputPriorityTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in inputDataDict. ID: {}".format(record['ID']))

    # Merge over the Priority Transaction data
    mergedDataDict['T1_PRIORITY_DKP_TABLE'] = masterDataDict['T1_PRIORITY_DKP_TABLE']
    mergedDataDict['T1_PRIORITY_TRANSACTIONS'] = masterDataDict['T1_PRIORITY_TRANSACTIONS']
    priorityIDsUniqueToInputDataDict = inputPriorityTransactionIDSet.difference(masterPriorityTransactionIDSet)
    for transactionID in priorityIDsUniqueToInputDataDict:
        for record in inputDataDict['T1_PRIORITY_TRANSACTIONS']:
            if record['ID'] == transactionID:
                # Read the DKP delta from this record and "replay" it by reflecting the change into the mergedDataDict
                player = record['Recipient']
                dkpDelta = record['DKPAfter'] - record['DKPBefore']
                if player not in mergedDataDict['T1_PRIORITY_DKP_TABLE']:
                    mergedDataDict['T1_PRIORITY_DKP_TABLE'][player] = dkpDelta
                else:
                    mergedDataDict['T1_PRIORITY_DKP_TABLE'][player] = mergedDataDict['T1_PRIORITY_DKP_TABLE'][player] + dkpDelta
                # Add the entire transaction record to the mergedDataDict
                mergedDataDict['T1_PRIORITY_TRANSACTIONS'].append(record)
                break

    # Create a Set of the 'ID's from each of the masterDataDict and inputDataDict 'LOTTERY_TRANSACTIONS' lists
    # Use Set operations to identify which Transactions are present in the inputDataDict but NOT the masterDataDict
    masterLotteryTransactionIDSet = set()
    for record in masterDataDict['T1_LOTTERY_TRANSACTIONS']:
        if record['ID'] not in masterLotteryTransactionIDSet:
            masterLotteryTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in masterDataDict. ID: {}".format(record['ID']))
    inputLotteryTransactionIDSet = set()
    for record in inputDataDict['T1_LOTTERY_TRANSACTIONS']:
        if record['ID'] not in inputLotteryTransactionIDSet:
            inputLotteryTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in inputDataDict. ID: {}".format(record['ID']))

    # Generate merged Lottery Transaction data
    mergedDataDict['T1_LOTTERY_DKP_TABLE'] = masterDataDict['T1_LOTTERY_DKP_TABLE']
    mergedDataDict['T1_LOTTERY_TRANSACTIONS'] = masterDataDict['T1_LOTTERY_TRANSACTIONS']
    lotteryIDsUniqueToInputDataDict = inputLotteryTransactionIDSet.difference(masterLotteryTransactionIDSet)
    for transactionID in lotteryIDsUniqueToInputDataDict:
        for record in inputDataDict['T1_LOTTERY_TRANSACTIONS']:
            if record['ID'] == transactionID:
                # Read the DKP delta from this record and "replay" it by reflecting the change into the mergedDataDict
                player = record['Recipient']
                dkpDelta = record['DKPAfter'] - record['DKPBefore']
                if player not in mergedDataDict['T1_LOTTERY_DKP_TABLE']:
                    mergedDataDict['T1_LOTTERY_DKP_TABLE'][player] = dkpDelta
                else:
                    mergedDataDict['T1_LOTTERY_DKP_TABLE'][player] = mergedDataDict['T1_LOTTERY_DKP_TABLE'][player] + dkpDelta
                # Add the entire transaction record to the mergedDataDict
                mergedDataDict['T1_LOTTERY_TRANSACTIONS'].append(record)
                break

    return mergedDataDict

def merge_t2_data(mergedDataDict, masterDataDict, inputDataDict):
    # Create a Set of the 'ID's from each of the masterDataDict and inputDataDict 'PRIORITY_TRANSACTIONS' lists
    # Use Set operations to identify which Transactions are present in the inputDataDict but NOT the masterDataDict
    masterPriorityTransactionIDSet = set()
    for record in masterDataDict['T2_PRIORITY_TRANSACTIONS']:
        if record['ID'] not in masterPriorityTransactionIDSet:
            masterPriorityTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in masterDataDict. ID: {}".format(record['ID']))
    inputPriorityTransactionIDSet = set()
    for record in inputDataDict['T2_PRIORITY_TRANSACTIONS']:
        if record['ID'] not in inputPriorityTransactionIDSet:
            inputPriorityTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in inputDataDict. ID: {}".format(record['ID']))

    # Merge over the Priority Transaction data
    mergedDataDict['T2_PRIORITY_DKP_TABLE'] = masterDataDict['T2_PRIORITY_DKP_TABLE']
    mergedDataDict['T2_PRIORITY_TRANSACTIONS'] = masterDataDict['T2_PRIORITY_TRANSACTIONS']
    priorityIDsUniqueToInputDataDict = inputPriorityTransactionIDSet.difference(masterPriorityTransactionIDSet)
    for transactionID in priorityIDsUniqueToInputDataDict:
        for record in inputDataDict['T2_PRIORITY_TRANSACTIONS']:
            if record['ID'] == transactionID:
                # Read the DKP delta from this record and "replay" it by reflecting the change into the mergedDataDict
                player = record['Recipient']
                dkpDelta = record['DKPAfter'] - record['DKPBefore']
                if player not in mergedDataDict['T2_PRIORITY_DKP_TABLE']:
                    mergedDataDict['T2_PRIORITY_DKP_TABLE'][player] = dkpDelta
                else:
                    mergedDataDict['T2_PRIORITY_DKP_TABLE'][player] = mergedDataDict['T2_PRIORITY_DKP_TABLE'][player] + dkpDelta
                # Add the entire transaction record to the mergedDataDict
                mergedDataDict['T2_PRIORITY_TRANSACTIONS'].append(record)
                break

    # Create a Set of the 'ID's from each of the masterDataDict and inputDataDict 'LOTTERY_TRANSACTIONS' lists
    # Use Set operations to identify which Transactions are present in the inputDataDict but NOT the masterDataDict
    masterLotteryTransactionIDSet = set()
    for record in masterDataDict['T2_LOTTERY_TRANSACTIONS']:
        if record['ID'] not in masterLotteryTransactionIDSet:
            masterLotteryTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in masterDataDict. ID: {}".format(record['ID']))
    inputLotteryTransactionIDSet = set()
    for record in inputDataDict['T2_LOTTERY_TRANSACTIONS']:
        if record['ID'] not in inputLotteryTransactionIDSet:
            inputLotteryTransactionIDSet.add(record['ID'])
        else:
            print("[WARN]: Somehow a duplicate Transaction ID was detected in inputDataDict. ID: {}".format(record['ID']))

    # Generate merged Lottery Transaction data
    mergedDataDict['T2_LOTTERY_DKP_TABLE'] = masterDataDict['T2_LOTTERY_DKP_TABLE']
    mergedDataDict['T2_LOTTERY_TRANSACTIONS'] = masterDataDict['T2_LOTTERY_TRANSACTIONS']
    lotteryIDsUniqueToInputDataDict = inputLotteryTransactionIDSet.difference(masterLotteryTransactionIDSet)
    for transactionID in lotteryIDsUniqueToInputDataDict:
        for record in inputDataDict['T2_LOTTERY_TRANSACTIONS']:
            if record['ID'] == transactionID:
                # Read the DKP delta from this record and "replay" it by reflecting the change into the mergedDataDict
                player = record['Recipient']
                dkpDelta = record['DKPAfter'] - record['DKPBefore']
                if player not in mergedDataDict['T2_LOTTERY_DKP_TABLE']:
                    mergedDataDict['T2_LOTTERY_DKP_TABLE'][player] = dkpDelta
                else:
                    mergedDataDict['T2_LOTTERY_DKP_TABLE'][player] = mergedDataDict['T2_LOTTERY_DKP_TABLE'][player] + dkpDelta
                # Add the entire transaction record to the mergedDataDict
                mergedDataDict['T2_LOTTERY_TRANSACTIONS'].append(record)
                break

    return mergedDataDict

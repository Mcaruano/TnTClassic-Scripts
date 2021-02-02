import addon_output_parser
import os
from progress.bar import IncrementalBar
import sys

def extract_only_loot_records(archiveFileData):
    lootRecords = []
    for key in archiveFileData.keys():
        if key.endswith('_TRANSACTIONS'):
            lootRecordsOnly = list(filter(lambda record: record['IsLootRecord'], archiveFileData[key]))
            for lootRecord in lootRecordsOnly:
                lootRecords.append(lootRecord)
    return lootRecords

if __name__ == "__main__":
    scriptPath = os.path.realpath(__file__)
    scriptDir = os.path.dirname(scriptPath)

    repoDir = os.path.abspath(os.path.join(scriptDir, os.pardir))
    outerDir = os.path.abspath(os.path.join(repoDir, os.pardir))
    archiveRepoPath = os.path.join(os.path.join(outerDir, 'TnTClassic-Archive'))
    archiveLuaFiles = list(filter(lambda fileName: fileName.endswith('.lua'), os.listdir(archiveRepoPath)))
    progress_bar = IncrementalBar("   Parsing Archive Files", max=len(archiveLuaFiles), suffix='%(percent)d%% ')
    lootRecords = []
    for archiveFile in archiveLuaFiles:
        archiveFileData = addon_output_parser.parse_addon_lua_file_to_dict(os.path.join(archiveRepoPath, archiveFile))
        lootRecords.extend(extract_only_loot_records(archiveFileData))
        progress_bar.next()

    progress_bar.finish()    
    
    print("\n{} Loot Records have been parsed".format(len(lootRecords)))
    # reverse=True sorts them from newest to oldest
    sortedLootRecords = sorted(lootRecords, key = lambda record: record['Timestamp'], reverse=True)

    sys.exit(0)
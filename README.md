# addon-and-backend-interface-scripts
Contains various scripts for manipulating/parsing the output from the various TnT AddOns. Details and Usage of the specific scripts below:

# addon_output_parser.py
**Description**: Takes the output of the TnTDKP AddOn and parses it into a Python Dictionary

**Purpose**: Provides an easy way to translate the AddOn output for use on our back-end

**Prerequisite**: The output from the TnTDKP AddOn must be present in the **addon_data/** directory. The file must be named *"TnTDKP.lua"*.

**Output**: None by default. There are methods that can be overridden to do what you wish with the data.

**Usage**: `python addon_output_parser.py`

# addon_lua_table_data_merger.py
**Description**: Takes the output of the TnTDKP AddOn from two separate players, and merges one into the other.

**Purpose**: This script is necessary due to us running split-Onyxia raids. After running two separate Onyxia raids, that data needs to be consolidated.

**Prerequisite**: The two data files must already be present in the **original_data/** directory. The files must be named *"TnTDKP.lua"* and *"TnTDKP_input.lua"*.

**Output**: The output of this script will be a file called *merged_addon_lua_data.txt* located in the **output/** directory.

**Usage**: `python addon_lua_table_data_merger.py`

# bank_inventory_auditor.py
**Description**: Takes the output of both the TnTBankTransactionMonitor and TnTCharacterBankSnapshotter AddOns, parses it, and performs an analysis for data discrepancies.

**Purpose**: The TnTCharacterBankSnapshotter AddOn represents the absolute truth of what is in our inventory, whereas the TnTBankTransactionMonitor monitors all inbound and outbound transactions in an effort to produce the same result. However, there are a number of obscure edge-cases I'm still ironing out with the TnTBankTransactionMonitor AddOn, so until those edge cases are settled, this script helps us maintain high integrity of our bank inventory.

**Prerequisite**: The *TnTBankTransactionMonitor.lua* **and** *TnTCharacterBankSnapshotter.lua* files from the AddOns must already be present in the **bank_data_files/** directory.

**Output**: If any discrepancies are found, a message indicating such will be printed to the terminal, together with a statement informing the user to check the summary file located at **output/bank_audit_results.txt**. *bank_audit_results.txt* has a bunch of useful information to help root out the data inconsistency, including the full transaction history (inbound and outbound) for the problematic ItemID.

**Usage**: `python bank_inventory_auditor.py`

# bank_inventory_parser.py
**Description**: Takes the output of the TnTBankTransactionMonitor AddOn and parses it into Python dictionaries

**Purpose**: Provides an easy way to translate the AddOn output for use on our back-end

**Prerequisite**: The *TnTBankTransactionMonitor.lua* file from the TnTBankTransactionMonitor AddOn must already be present in the **bank_data/** directory.

**Output**: None by default. There are methods that can be overridden to do what you wish with the data.

**Usage**: `python bank_inventory_parser.py`

# dkp_and_list_python_objs_to_lua_table_converter.py
**Description**: This script simply takes some Python Dictionaries containing the Priority/Lottery Registries and Table objects containing Priority/Lottery DKP Tuples and spits it out in Lua table syntax such that it can be "loaded" into the TnTDKP AddOn.

**Purpose**: Eventually we will have an API on the backend that simply generates the desired Lua file with the latest data. Until then, this is an easy-enough stop-gap where I simply copy the raw Python data structures from the gitlab repo into the head of the python script.

**Prerequisite**: The latest data must be copied from the gitlab

**Output**: Running this script will generate a timestamped Lua file of the format: *TnTDKPData_10_22_2019-17_33.lua*. Appending the timestamp to the filename is a simple mechanism to ensure the user when the data was gathered.

**Usage**: `python dkp_and_list_python_objs_to_lua_table_converter.py`

**"Loading" the data into the AddOn:** To load the data into the data, the following steps must be followed IN THIS ORDER:
1. The player must exit out of the game
2. The player must rename the *TnTDKPData\*.txt* file to *TnTDKP.lua*
3. The player must _delete_ the existing TnTDKP.lua file in their **WTF/Account/<account_name>/SavedVariables** folder
4. The player must place the new TnTDKP.lua file into their **WTF/Account/<account_name>/SavedVariables** 
5. The player must then log into the game. They should now see the new data
# coding=utf-8

# This is a basic map that transforms each player's Discord username into the
# name of their main character. If a player is not present in this list, then
# they either changed their Discord name, or they haven't been added to this list yet.
# I've added everyone to this list even if their Discord name matches their in-game name,
# this way if any name is processed that is not present in this list it can be raised as
# an immediate red flag.

DISCORD_NAME_MAPPING = {
    "Abstinence": "Abstinence",
    "Airth": "Airth",
    "Akaran": "Akaran",
    "Aro": "Aro",
    "Ashori": "Ashori",
    "Baopi": "Baopi",
    "BERZERK": "Berzerk",
    "Blisterz": "Sofakinglulz",
    "Bunneh": "Bunnéh",
    "Chocothunda": "Haties",
    "chuunin": "Chuunin",
    "Dalran": "Dalran",
    "Demeker": "Demeker",
    "dienasty": "Dienasty",
    "Digie": "Digie",
    "Drunkinrage": "Drunkinrage",
    "deerizzy/drizz": "Youngdrizzy",
    "Ekohz": "Ekohz",
    "EllieVyra": "Ellievyra",
    "Ellwindelm": "Ellwindelm",
    "Emianne": "Emianne",
    "fearbot": "Fearbot",
    "Fjori": "Whiskeysour",
    "Frosted": "Realfrosted",
    "Galm": "Galm",
    "Glimfolkor": "Glimfolkor",
    "GoodJorb": "Goodjorb",
    "Haties": "Haties",
    "hatty": "Jerillak",
    "Hyolin": "Envisage",
    "Hyolin/Envishi": "Envisage",
    "hulkhigginz": "Hulkhigginz",
    "jerillak": "Jerillak",
    "Justin": "Justin",
    "Kang": "Kang",
    "Kiele": "Kiele",
    "Kortey": "Kortey",
    "lilkill": "Lilkill",
    "Lilkittygato": "Lilkittygato",
    "LKG": "Lilkittygato",
    "Lovesmehot": "Lovesmehot",
    "Lynn(Caeland": "Caelandine",
    "Lynn(Caelandi": "Caelandine",
    "Lynn(Caelandin": "Caelandine",
    "Malchazor": "Malchazor",
    "Minty": "Mintychan",
    "MLG": "Mlg",
    "Nocjr": "Nocjr",
    "Nynisa": "Nynisa",
    "Phi": "Phi",
    "pikachau": "Raichau",
    "Pudzey": "Pudzey",
    "Radi": "Radicola",
    "rotheart": "Rotheart",
    "Roodolph": "Roodolph",
    "Roodolph/Rudol": "Roodolph",
    "Rudolf(Golde": "Roodolph",
    "Rudolf(Golden": "Roodolph",
    "Rudolf/Roodo": "Roodolph",
    "Rudolf/Roodolp": "Roodolph",
    "rumeboy": "Rumegirl",
    "Sapper": "Sapper",
    "Salchant": "Salchant",
    "scrodo/poeki": "Scrodo",
    "scrodo/poekin": "Scrodo",
    "Sean(Kaylä)": "Kaylä",
    "sekdar(sekjr": "Sekjr",
    "sekdar(sekjr)": "Sekjr",
    "Sheol/Soupz": "Sheol",
    "Shnackypacky": "Shnackypacky",
    "Simptease": "Simptease",
    "Sizzlenips-A": "Sizzleñips",
    "Sizzlenips-Ark": "Sizzleñips",
    "Snickercakes": "Snickercakes",
    "Solljus/Verm": "Vermora",
    "Stephany": "Stephany",
    "suWACO": "Suwuavo",
    "Sylador": "Sylador",
    "Thursday": "Thursday",
    "Tongsta": "Tongster",
    "Venjamen": "Venjamen",
    "Vermora": "Vermora",
    "Whogryps": "Whogryps",
    "Zoff": "Zóff",
    "Zerxx": "Zerxx",
}

def resolveName(discordName):
    return DISCORD_NAME_MAPPING[discordName]
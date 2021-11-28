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
    "Barlen": "Barlen",
    "BERZERK": "Berzerk",
    "Blisterz": "Sofakinglulz",
    "Brittany": "Brittany",
    "barnabris(": "Barnabris",
    "barnabris(hul": "Barnabris",
    "barnabris(hulk)": "Barnabris",
    "ChubR0ck": "Chubrock",
    "chuunin": "Chuunin",
    "CrazyDaisy": "Crazydaisy",
    "Dalran": "Dalran",
    "Demeker": "Demeker",
    "dienasty": "Dienasty",
    "Digie": "Digie",
    "Digie/Nekr": "Digie",
    "Digie/Nekryss": "Digie",
    "Drunkinrage": "Drunkinrage",
    "deerizzy/drizz": "Youngdrizzy",
    "EllieVyra": "Ellievyra",
    "Ellwindelm": "Ellwindelm",
    "Envisage/Hyoli": "Hyolin",
    "Envisage/Hyol": "Hyolin",
    "Fjori": "Whiskeysour",
    "Galm": "Galm",
    "Glimfolkor": "Glimfolkor",
    "GoodJorb": "Goodjorb",
    "Goodjorb": "Goodjorb",
    "Hyolin": "Hyolin",
    "Hyolin/Env": "Hyolin",
    "Hyolin/Envi": "Hyolin",
    "Hyolin/Envishi": "Hyolin",
    "Hulkhigginz": "Barnabris",
    "hulkhigginz": "Barnabris",
    "itssolzarnow(": "Solzar",
    "Jahmee": "Jahmee",
    "Justin": "Justin",
    "Kang": "Kang",
    "Kiele": "Kiele",
    "Kinasa": "Kinastra",
    "Kinastra": "Kinastra",
    "kharagan": "Kharagan",
    "Kortey": "Korteh",
    "Krumson": "Krumonx",
    "Lovesmehot": "Lovesmehot",
    "Lynn(Caeland": "Caelandine",
    "Lynn(Caelandi": "Caelandine",
    "Lynn(Caelandin": "Caelandine",
    "Lynn(Caelandine)": "Caelandine",
    "Malchazor": "Malchazor",
    "Mitchel": "Mitchendo",
    "Mitchendo": "Mitchendo",
    "MLG": "Mlg",
    "Murduc": "Murduc",
    "Nashy": "Nashy",
    "NukeJr(Searious)": "Searious",
    "NukeJr(Seario": "Searious",
    "Nynisa": "Nynisa",
    "Peacard": "Peacard",
    "Phi": "Phi",
    "pikachau": "Pikachau",
    "Radi": "Radicola",
    "Raya": "Rayas",
    "Reminosc": "Spookyremi",
    "rotheart": "Rotheart",
    "Riko": "Riko",
    "Roodolph": "Roodolph",
    "Roodolph/Rudol": "Roodolph",
    "Rudolf(Golde": "Roodolph",
    "Rudolf(Golden": "Roodolph",
    "Rudolf/Roodo": "Roodolph",
    "Rudolf/Roodolp": "Roodolph",
    "rumeboy": "Rumegirl",
    "Salchant": "Salchant",
    "Schroumpf": "Schroumpf",
    "scrodo/poeki": "Scrodo",
    "scrodo/poekin": "Scrodo",
    "Sean(Kaylä)": "Kaylä",
    "Searious": "Searious",
    "Seion": "Zeion",
    "sekdar(sek": "Sekkondary",
    "sekdar(sekjr": "Sekkondary",
    "sekdar(sekjr)": "Sekkondary",
    "sekdar(sekkon": "Sekkondary",
    "sekdar(sekkondary)": "Sekkondary",
    "Sheol/Soupz": "Sheol",
    "Shnacks": "Shnacks",
    "Simptease": "Wildshrimp",
    "Sizzlenips": "Sizzleñips",
    "Sizzlenips-A": "Sizzleñips",
    "Sizzlenips-Ar": "Sizzleñips",
    "Sizzlenips-Ark": "Sizzleñips",
    "Skypola": "Skypola",
    "Snickercakes": "Snickercakes",
    "Solljus/Verm": "Vermora",
    "SolzaroftheBl": "Solzar",
    "SolzaroftheBloodFurnace": "Solzar",
    "Stephany": "Stephany",
    "Sylador": "Sylador",
    "Telyris": "Velyris",
    "Tenfour": "Tenfour",
    "Thaladred(Cra": "Crazydaisy",
    "Thejudge": "Thejudge",
    "Venjamen": "Venjamen",
    "Venjamin": "Venjamen",
    "Vermora": "Vermora",
    "Wildshrimp": "Wildshrimp",
    "Zerxx": "Zerxx",
}

def resolveName(discordName):
    return DISCORD_NAME_MAPPING[discordName]
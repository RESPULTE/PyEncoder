import string
import yaml
import math
from typing import Dict

try:
    with open("./src/pyencoder/config.yaml", "r") as stream:
        Config: Dict[str, Dict] = yaml.safe_load(stream)
except yaml.YAMLError as err:
    raise Exception("failed on startup: cannot instantiate config") from err

Config["SYMBOLS"] = string.printable + Config["EOF_MARKER"]
Config["NUM_SYMBOLS"] = len(Config["SYMBOLS"])

Config["FIXED_CODE_SIZE"] = math.ceil(math.log2(Config["NUM_SYMBOLS"]))
Config["FIXED_CODE_LOOKUP"] = {
    k: "{num:0{size}b}".format(num=i, size=Config["FIXED_CODE_SIZE"]) for i, k in enumerate(Config["SYMBOLS"])
}
Config["FIXED_SYMBOL_LOOKUP"] = {v: k for k, v in Config["FIXED_CODE_LOOKUP"].items()}

import string
from typing import Dict
import yaml

try:
    with open("./src/pyencoder/config.yaml", "r") as stream:
        Config: Dict[str, Dict] = yaml.safe_load(stream)
except yaml.YAMLError as err:
    raise Exception("failed on startup: cannot instantiate config") from err

Config["SYMBOLS"] = string.printable + Config["EOF_MARKER"]
Config["NUM_SYMBOLS"] = len(Config["SYMBOLS"])

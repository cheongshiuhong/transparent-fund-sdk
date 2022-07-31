# Standard libraries
from pathlib import Path
import json

# 3rd party libraries
from web3.contract import ABI


def load_abi(dir_path: str, abi_path: str = "") -> ABI:
    with open(Path(dir_path).parent / (abi_path or "abi.json"), "r") as f:
        return json.load(f)

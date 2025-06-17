from pathlib import Path
import json
import pytest

from schemas import configuration

BASE_DIR = Path(__file__).parent

only_devices = BASE_DIR / "configs" / "one_device.json"

def test_json_config():
    with open(only_devices) as file:
        config = json.load(file)
        assert configuration.validate(config) is not None

    
    

from pathlib import Path
import json
import pytest

from schemas import configuration

BASE_DIR = Path(__file__).parent

one_device = BASE_DIR / "configs" / "one_device.json"
multiple_devices = BASE_DIR / "configs" / "multiple_devices.json"
devices_with_networks = BASE_DIR / "configs" / "devices_with_networks.json"

def test_json_config():
    with open(one_device) as file:
        config = json.load(file)
        assert configuration.validate(config) is not None

    with open(multiple_devices) as file:
        config = json.load(file)
        assert configuration.validate(config) is not None

    with open(devices_with_networks) as file:
        config = json.load(file)
        assert configuration.validate(config) is not None


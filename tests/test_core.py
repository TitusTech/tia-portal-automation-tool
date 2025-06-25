from pathlib import Path
import json
import pytest

from src.core import core
from src.schemas import configuration
import src.modules.Portals as Portals

BASE_DIR = Path(__file__).parent

multiple_devices = BASE_DIR / "configs" / "multiple_devices.json"
multiple_devices_with_libraries = BASE_DIR / "configs" / "multiple_devices_with_libraries.json"
multiple_devices_with_local_modules = BASE_DIR / "configs" / "multiple_devices_with_local_modules.json"
multiple_devices_with_plc_data_types = BASE_DIR / "configs" / "multiple_devices_with_plc_data_types.json"
plc_tags = BASE_DIR / "configs" / "plc_tags.json"

dlls = core.generate_dlls()
dll = dlls['V18']

import clr
from System.IO import DirectoryInfo, FileInfo
clr.AddReference(dll.as_posix())
import Siemens.Engineering as SE

imports = Portals.Imports(SE, DirectoryInfo, FileInfo)

def test_core():
    config = None
    with open(multiple_devices) as file:
        config = configuration.validate(json.load(file))
    config['directory'] = BASE_DIR.parent.parent.parent
    config['name'] = f"test_core.{multiple_devices.stem}"

    TIA = core.execute(imports, config, { "enable_ui": True, })

def test_core_local_modules():
    config = None
    with open(multiple_devices_with_local_modules) as file:
        config = configuration.validate(json.load(file))
    config['directory'] = BASE_DIR.parent.parent.parent
    config['name'] = f"test_core.{multiple_devices_with_local_modules.stem}"

    TIA = core.execute(imports, config, { "enable_ui": True, })

def test_core_plc_tags():
    config = None
    with open(plc_tags) as file:
        config = configuration.validate(json.load(file))
    config['directory'] = BASE_DIR.parent.parent.parent
    config['name'] = f"test_core.{plc_tags.stem}"

    TIA = core.execute(imports, config, { "enable_ui": True, })

def test_core_libraries():
    config = None
    with open(multiple_devices_with_libraries) as file:
        config = configuration.validate(json.load(file))
    config['directory'] = BASE_DIR.parent.parent.parent
    config['name'] = f"test_core.{multiple_devices_with_libraries.stem}"

    TIA = core.execute(imports, config, { "enable_ui": True, })

def test_core_plc_data_types():
    config = None
    with open(multiple_devices_with_plc_data_types) as file:
        config = configuration.validate(json.load(file))
    config['directory'] = BASE_DIR.parent.parent.parent
    config['name'] = f"test_core.{multiple_devices_with_plc_data_types.stem}"

    TIA = core.execute(imports, config, { "enable_ui": True, })

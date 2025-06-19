from pathlib import Path
import json
import pytest

from core import core
from schemas import configuration
import modules.Portals as Portals

BASE_DIR = Path(__file__).parent

multiple_devices = BASE_DIR / "configs" / "multiple_devices.json"
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
    config['directory'] = BASE_DIR.parent.parent
    config['name'] = f"test_core.{multiple_devices.stem}"

    project = core.execute(imports, config, { "enable_ui": True, })


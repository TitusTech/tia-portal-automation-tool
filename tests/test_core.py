from pathlib import Path
import json
import pytest

from core import core
from schemas import configuration
import modules.Portals as Portals

BASE_DIR = Path(__file__).parent

devices_with_networks = BASE_DIR / "configs" / "devices_with_networks.json"

def test_core():
    config = None
    with open(devices_with_networks) as file:
       config = configuration.validate(json.load(file))
    dlls = core.generate_dlls()
    dll = dlls['V18']

    config['directory'] = BASE_DIR
    config['name'] = f"test_core.{devices_with_networks.stem}"

    import clr
    from System.IO import DirectoryInfo, FileInfo

    clr.AddReference(dll.as_posix())
    import Siemens.Engineering as SE

    imports = Portals.Imports(SE, DirectoryInfo, FileInfo)
    core.execute(imports, config, { "enable_ui": True, })


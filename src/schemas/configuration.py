from __future__ import annotations
from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.Devices import PLC
from src.schemas.DeviceItems import DeviceItem
from src.schemas.PlcTags import PlcTagTable
from src.schemas.Libraries import GlobalLibrary

root = Schema(
    {
        Optional("overwrite", default=True): bool,
        Optional("devices", default=[]): And(list, [Or(PLC)]),
        Optional("Local modules", default=[]): And(list, [DeviceItem]),
        Optional("PLC tags", default=[]): And(list, [PlcTagTable]),
        Optional("libraries", default=[]): And(list, [GlobalLibrary]),
    },
    ignore_extra_keys=True  
)

def validate(data):
    return root.validate(data)

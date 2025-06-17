from __future__ import annotations
from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

from schemas.Devices import PLC
from schemas.Networks import Network

root = Schema(
    {
        Optional("overwrite", default=True): bool,
        Optional("devices", default=[]): And(list, [Or(PLC)]),
        Optional("networks", default=[]): [Network],
    },
    ignore_extra_keys=True  
)

def validate(data):
    return root.validate(data)

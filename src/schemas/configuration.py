from __future__ import annotations
from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.BlocksGlobalDB import GlobalDB
from src.schemas.DeviceItems import DeviceItem
from src.schemas.Devices import PLC
from src.schemas.Libraries import GlobalLibrary
from src.schemas.NetworkSources import NetworkSource, Instance
from src.schemas.PlcDataTypes import PlcDataType
from src.schemas.BlocksFB import FunctionBlock
from src.schemas.BlocksOB import OrganizationBlock
from src.schemas.PlcTags import PlcTagTable

root = Schema(
    {
        Optional("overwrite", default=True): bool,
        Optional("devices", default=[]): And(list, [Or(PLC)]),
        Optional("Local modules", default=[]): And(list, [DeviceItem]),
        Optional("PLC tags", default=[]): And(list, [PlcTagTable]),
        Optional("PLC data types", default=[]): And(list, [PlcDataType]),
        Optional("libraries", default=[]): And(list, [GlobalLibrary]),
        Optional("Program blocks", default=[]): And(list, [Or(OrganizationBlock, FunctionBlock, GlobalDB)]),
        Optional("Network sources", default=[]): And(list, [NetworkSource]),
        Optional("Instances", default=[]): And(list, [Instance]),
    },
    ignore_extra_keys=True  
)

def validate(data):
    return root.validate(data)

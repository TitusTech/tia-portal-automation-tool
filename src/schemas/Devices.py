from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.Networks import NetworkInterface

Device = Schema({
    "id": int,
    "p_name": str, # PLC1
    "p_typeIdentifier": str, # OrderNumber:6ES7 510-1DJ01-0AB0/V2.0
    Optional("network_interface", default={}): NetworkInterface,
    Optional("required_libraries", default=[]): list[str],
})

PLC = Schema({
    **Device._schema,
    "p_deviceName": str, # NewPlcDevice
    Optional("slots_required", default=2): int,
})


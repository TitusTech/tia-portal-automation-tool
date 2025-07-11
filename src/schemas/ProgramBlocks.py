from schema import Schema, And, Or, Use, Optional, SchemaError

from src.modules.XML.ProgramBlocks import PlcEnum, DatabaseEnum, VariableSection, VariableStruct

VariableStruct = Schema({
    "name": str,
    "datatype": str,
    Optional("retain", default=True): bool,
    Optional("start_value", default=""): str,
    Optional("attributes", default={}): dict,
})

VariableSection = Schema({
    "plc_block_id": int,
    "name": str,
    "data": And(list, [VariableStruct]),
})

PlcBlock = Schema({
    "DeviceID": int,
    "id": int,
    Optional("network_source_id"): int,
    "type": And(str, Use(PlcEnum)),
    "name": str,
    Optional("blockgroup_path", default="/"): str,
    Optional("number", default=1): int,
})

Parameter = Schema({
    "plc_block_id": int,
    "parameters": dict,
})

Database = Schema({
    "DeviceID": int,
    "id": int,
    "type": And(str, Use(DatabaseEnum)),
    "name": str,
})

InstanceDB = Schema({
    **Database._schema,
    Optional("blockgroup_path", default="/"): str,
    Optional("number", default=1): int,
})

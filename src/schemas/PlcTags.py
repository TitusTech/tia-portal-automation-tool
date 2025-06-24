from schema import Schema, And, Or, Use, Optional, SchemaError


PlcTag = Schema({
    "Name": str,
    "DataTypeName": str,
    "LogicalAddress": str,
})

PlcTagTable = Schema({
    "DeviceID": int,
    "Name": str,
    Optional("Tags", default=[]): [PlcTag],
})

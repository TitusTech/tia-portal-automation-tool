from schema import Schema, And, Or, Use, Optional, SchemaError

DeviceItem = Schema({
    "DeviceID": int,
    "typeIdentifier": str,
    "name": str,
    "positionNumber": int,
})

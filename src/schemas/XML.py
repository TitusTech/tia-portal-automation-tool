from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

PlcStruct = Schema({
    "Name": str,
    "Datatype": str,
    Optional("attributes", default={}): dict,
})

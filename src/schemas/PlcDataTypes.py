from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.XML import PlcStruct

PlcDataType = Schema({
    "Name": str,
    Optional("types", default=[]): [PlcStruct],
})

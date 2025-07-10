from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.ProgramBlocks import InstanceDB, VariableStruct

GlobalDB = Schema({
    **InstanceDB._schema,
    Optional("structs", default=[]): And(list, [VariableStruct]),
    Optional("attributes", default={}): dict,
})

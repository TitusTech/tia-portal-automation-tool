from schema import Schema, And, Use

from src.modules.BlocksDBInstances import CallOptionEnum
from src.schemas.ProgramBlocks import Database


# SingleInstance = Schema({
#     **Database._schema,
#     "plc_block_id": int,
#     "call_option": CallOptionEnum.Single.value
# })
#
# MultiInstance = Schema({
#     **Database._schema,
#     "plc_block_id": int,
#     "call_option": CallOptionEnum.Multi.value
# })
#
# ParameterInstance = Schema({
#     **Database._schema,
#     "plc_block_id": int,
#     "call_option": CallOptionEnum.Parameter.value
# })

InstanceDB = Schema({
    **Database._schema,
    "plc_block_id": int,
    "call_option": And(str, Use(CallOptionEnum))
})

from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.PlcOB import OrganizationBlock
from src.schemas.PlcFB import FunctionBlock

NetworkSource = Schema({
    "plc_block_id": int,
    "id": int,
    Optional("instances", default=[]): And(list, [Or(OrganizationBlock, FunctionBlock)]),
    # Optional("instances", default=[]): And(list, [Or(schema_instance_source, schema_instance_library, OrganizationBlock)]),
    Optional("title", default=""): str,
    Optional("comment", default=""): str,
})


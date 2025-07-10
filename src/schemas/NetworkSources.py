from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.BlocksOB import OrganizationBlock
from src.schemas.BlocksFB import FunctionBlock

NetworkSource = Schema({
    "plc_block_id": int,
    "id": int,
    Optional("title", default=""): str,
    Optional("comment", default=""): str,
})

Instance = Schema({
    "network_source_id": int,
    "instance": Or(OrganizationBlock, FunctionBlock),
    # Optional("instances", default=[]): And(list, [Or(schema_instance_source, schema_instance_library, OrganizationBlock)]),
})

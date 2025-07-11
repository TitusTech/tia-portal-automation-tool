from schema import Schema, And, Or, Use, Optional, SchemaError

from src.schemas.ProgramBlocks import PlcBlock

FunctionBlock = Schema({
    **PlcBlock.schema,
    "programming_language": str,
    Optional("is_instance", default=False): bool,
    # Optional("db"): Or(schema_instancedb, schema_db),
})

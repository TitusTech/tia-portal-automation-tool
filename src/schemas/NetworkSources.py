from schema import Schema, Optional, And


NetworkSource = Schema({
    "id": int,
    "plc_block_id": int,
    Optional("title", default=""): str,
    Optional("comment", default=""): str,
})

WireParameter = Schema({
    "plc_block_id": int,
    "parameters": {str: str},
})

WireTemplate = Schema({
    "block_name": str,
    "parameters": And(list, [Schema({
        "name": str,
        "section": str,
        "datatype": str,
        "value": str,
        Optional("negated", default=False): bool,
    })]),
})

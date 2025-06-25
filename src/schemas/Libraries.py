from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

GlobalLibrary = Schema({
    "path": And(str, Use(Path), lambda p: Path(p)),
    Optional("read_only", default=True): bool,
})

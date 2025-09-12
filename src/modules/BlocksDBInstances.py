from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
import logging

from src.core import logs

from src.modules.BlocksDatabase import Database
from src.modules.ProgramBlocks import locate_blockgroup

logs.setup(logging.DEBUG)
logger = logging.getLogger(__name__)


class CallOptionEnum(Enum):
    Single = "Single"
    Multi = "Multi"
    Parameter = "Parameter"


@dataclass
class InstanceDB(Database):
    Id: int
    InstanceOfName: str
    Name: str
    CallOption: CallOptionEnum
    Number: int
    BlockGroupPath: PurePosixPath


def create(plc_software: Siemens.Engineering.HW.Software,
           data: InstanceDB
           ):
    if not data.InstanceOfName:
        return

    logger.info(f"Generation of InstanceDB {data.Name} of Instance {
                data.InstanceOfName} started")

    db_name = data.Name if data.Name != "" else f"{data.InstanceOfName}_DB"

    blockgroup = locate_blockgroup(
        plc_software, data.BlockGroupPath, mkdir=True)
    blockgroup.Blocks.CreateInstanceDB(
        db_name, True, data.Number, data.InstanceOfName)

from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath

from src.modules.XML.ProgramBlocks import Base, ProgramBlock


@dataclass
class Function(ProgramBlock):
    DeviceID: int
    BlockGroupPath: PurePosixPath
    IsInstance: bool
    LibraryData: LibraryData


class XML(Base):
    DOCUMENT = "SW.Blocks.FC"

    def __init__(self, data: ProgramBlock) -> None:
        super().__init__(data.Name, data.Number, data.ProgrammingLanguage, data.Variables)

        self._create_input_section()
        self._create_output_section()
        self._create_inout_section()
        self._create_temp_section()
        self._create_constant_section()
        self._create_return_section()

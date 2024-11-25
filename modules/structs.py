from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Union
import xml.etree.ElementTree as ET

class OBEventClass(Enum):
    ProgramCycle = "ProgramCycle"
    Startup = "Startup"
    # extend

class DocumentSWType(Enum):
    TypesPlcStruct = "SW.Types.PlcStruct"
    BlocksOB = "SW.Blocks.OB"
    BlocksFB = "SW.Blocks.FB"
    BlocksFC = "SW.Blocks.FC"
    BlocksGlobalDB = "SW.Blocks.GlobalDB"



class XMLNS(Enum):
    SECTIONS = "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    FLGNET = "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v4"



@dataclass
class PlcStructData:
    Name: str
    Types: list

@dataclass
class SWBlockData:
    Name: str
    Number: int
    ProgrammingLanguage: str
    NetworkSources: list[NetworkSourceContainer]

@dataclass
class OBData(SWBlockData):
    EventClass: OBEventClass = OBEventClass.ProgramCycle


class Source(Enum):
    LIBRARY = "LIBRARY"
    LOCAL = "LOCAL"


@dataclass
class ProjectData:
    Name: str
    Directory: Path
    Overwrite: bool

@dataclass
class LibraryData:
    FilePath: Path
    ReadOnly: bool

@dataclass
class DeviceCreationData:
    TypeIdentifier: str
    Name: str
    DeviceName: str

@dataclass
class MasterCopiesDeviceData:
    Libraries: list[str]


@dataclass
class ModuleData:
    TypeIdentifier: str
    Name: str
    PositionNumber: int

@dataclass
class ModulesContainerData:
    LocalModules: list[ModuleData]
    HmiModules: list[ModuleData]
    SlotsRequired: int


@dataclass
class TagData:
    Name: str
    DataTypeName: str
    LogicalAddress: str

@dataclass
class TagTableData:
    Name: str
    # Tags: list[TagData]


@dataclass
class InstanceData:
    Type: Source
    Name: str
    FromFolder: list[str]
    ToFolder: list[str]

@dataclass
class LibraryInstanceData(InstanceData):
    Library: str

@dataclass
class NetworkSourceData:
    Instances: list[Union[InstanceData, LibraryInstanceData, PlcBlockData]]
    Title: str
    Comment: str

@dataclass
class ProgramBlockData:
    Type: DocumentSWType
    Name: str
    Folder: list[str]
    Number: int


@dataclass
class PlcBlockData(ProgramBlockData):
    ProgrammingLanguage: str
    NetworkSources: list[NetworkSourceData]


@dataclass
class NetworkSourceContainer:
    Title: str
    Comment: str
    Instances: list


@dataclass
class InstanceContainer:
    Name: str
    BlockType: str

@dataclass
class ProgramBlockContainer:
    Type: DocumentSWType
    Name: str
    Number: int

@dataclass
class PlcBlockContainer(ProgramBlockContainer):
    ProgrammingLanguage: str
    NetworkSources: list[NetworkSourceContainer]


@dataclass
class DatabaseBlockData(ProgramBlockData):
    InstanceType: str




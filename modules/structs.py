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
    PlcWatchTable = "SW.WatchAndForceTables.PlcWatchTable"
    PlcForceTable = "SW.WatchAndForceTables.PlcForceTable"
    PlcWatchTableEntry = "SW.WatchAndForceTables.PlcWatchTableEntry"
    PlcForceTableEntry = "SW.WatchAndForceTables.PlcForceTableEntry"


class DatabaseType(Enum):
    InstanceDB = "SW.Blocks.InstanceDB"
    GlobalDB = "SW.Blocks.GlobalDB"
    ArrayDB = "SW.Blocks.ArrayDB"
    MultiInstance = "MultiInstance"


class XMLNS(Enum):
    SECTIONS = "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    FLGNET = "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v4"


class PlcWatchForceType(Enum):
    PlcWatchTable = "PlcWatchTable"
    PlcForceTable = "PlcForceTable"

@dataclass
class PlcStructData:
    Name: str
    Types: list


@dataclass
class VariableStruct:
    Name: str
    Datatype: str
    Retain: bool
    StartValue: str
    Attributes: dict

@dataclass 
class VariableSection:
    Name: str
    Variables: list[VariableStruct]

@dataclass
class SWBlockData:
    Name: str
    Number: int
    ProgrammingLanguage: str
    Variables: list[VariableSection]

@dataclass
class OBData(SWBlockData):
    NetworkSources: list[NetworkSourceContainer]
    EventClass: OBEventClass

@dataclass
class FBData(SWBlockData):
    NetworkSources: list[NetworkSourceContainer]

class Source(Enum):
    LIBRARY = "LIBRARY"
    LOCAL = "LOCAL"


@dataclass
class ProjectData:
    Name: str
    Directory: Path
    Overwrite: bool

@dataclass
class InstanceParameterTemplate:
    Name: str
    Parameters: list[WireParameter]

@dataclass
class LibraryConfigData:
    Template: Path

@dataclass
class LibraryData:
    FilePath: Path
    ReadOnly: bool
    Config: LibraryConfigData

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
class DatabaseData:
    Type: DatabaseType
    Name: str
    Folder: list[str]
    Number: int


@dataclass
class GlobalDBData(DatabaseData):
    Structs: list[VariableStruct]
    Attributes: dict



@dataclass
class WireParameter:
    Name: str
    Section: str
    Datatype: str
    Value: str | list[str]
    Negated: bool

@dataclass
class InstanceData:
    Source: Source
    Type: DocumentSWType
    Name: str
    Number: int
    FromFolder: str | list[str]
    ToFolder: str | list[str]
    Database: DatabaseData
    Parameters: list[WireParameter]

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
    Type: DocumentSWType | DatabaseType
    Name: str
    Folder: list[str]
    Number: int


@dataclass
class PlcBlockData(ProgramBlockData):
    ProgrammingLanguage: str
    NetworkSources: list[NetworkSourceData]
    Database: DatabaseData
    Variables: list[VariableSection]
    Parameters: list[WireParameter]

@dataclass
class NetworkSourceContainer:
    Title: str
    Comment: str
    Instances: list


@dataclass
class InstanceContainer:
    Name: str
    Type: DocumentSWType
    Database: DatabaseData
    Parameters: list[WireParameter]


@dataclass
class ProgramBlockContainer:
    Type: DocumentSWType | DatabaseType
    Name: str
    Number: int
    Parameters: list[WireParameter]


@dataclass
class PlcBlockContainer(ProgramBlockContainer):
    ProgrammingLanguage: str
    NetworkSources: list[NetworkSourceContainer]
    Database: DatabaseData
    Variables: list[VariableSection]



@dataclass
class WatchForceTable:
    Name: str
    Address: str
    DisplayFormat: str
    MonitorTrigger: str

@dataclass
class PlcForceTableEntryData(WatchForceTable):
    ForceIntention: bool
    ForceValue: str

@dataclass
class PlcWatchTableEntryData(WatchForceTable):
    ModifyIntention: bool
    ModifyTrigger: str
    ModifyValue: str


@dataclass
class WatchAndForceTablesData:
    Type: PlcWatchForceType
    Name: str
    Entries: list[PlcForceTableEntryData | PlcWatchTableEntryData]


@dataclass
class SubnetData:
    Name: str
    Address: str
    IoController: str


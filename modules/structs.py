from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Union
import xml.etree.ElementTree as ET

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
class DeviceCreationData:
    TypeIdentifier: str
    Name: str
    DeviceName: str

@dataclass
class SubnetData:
    Name: str
    Address: str
    IoController: str


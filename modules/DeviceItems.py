from __future__ import annotations
from dataclasses import dataclass

@dataclass
class DeviceItem:
    DeviceID: int
    typeIdentifier: str
    name: str
    positionNumber: int




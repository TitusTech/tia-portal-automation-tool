from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import xml.etree.ElementTree as ET

from src.modules.XML.Documents import Document

class Software(Document):
    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.Section = ET.SubElement(self.Sections, "Section", attrib={'Name': "None"})


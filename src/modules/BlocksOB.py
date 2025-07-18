from dataclasses import dataclass
from enum import Enum
import xml.etree.ElementTree as ET

from src.modules.XML.ProgramBlocks import Base, PlcEnum, ProgramBlock, NetworkSource, BlockCompileUnit


class EventClassEnum(Enum):
    ProgramCycle = "ProgramCycle"
    Startup = "Startup"


@dataclass
class OrganizationBlock(ProgramBlock):
    NetworkSources: list[NetworkSource]
    EventClass: EventClassEnum


class OB(Base):
    DOCUMENT = PlcEnum.OrganizationBlock.value

    def __init__(self, data: OrganizationBlock) -> None:
        # EventClasses have different number rules
        data.Number = max(123, min(data.Number, 32767)
                          ) if data.Number != 1 else 1
        super().__init__(data.Name, data.Number, data.ProgrammingLanguage, data.Variables)

        # default is ProgramCycle
        ET.SubElement(self.AttributeList,
                      "SecondaryType").text = data.EventClass.value
        self._create_input_section()
        self._create_temp_section()
        self._create_constant_section()
        ET.SubElement(self.InputSection, "Member", attrib={
            "Name": "Initial_Call",
            "Datatype": "Bool",
            "Informative": "true",
        })
        ET.SubElement(self.InputSection, "Member", attrib={
            "Name": "Remanence",
            "Datatype": "Bool",
            "Informative": "true",
        })

        id = 3
        for network_source in data.NetworkSources:
            CompileUnit = BlockCompileUnit(
                data.ProgrammingLanguage, network_source, id).root
            self.ObjectList.append(CompileUnit)
            id += 5

from dataclasses import dataclass
import xml.etree.ElementTree as ET

from src.modules.XML.ProgramBlocks import VariableSection, Database
from src.modules.XML.ProgramBlocks import Base


@dataclass
class DataBlock(Database):
    VariableSections: list[VariableSection]
    Attributes: dict


class GlobalDB(Base):
    DOCUMENT = "SW.Blocks.GlobalDB"

    def __init__(self, data: DataBlock):
        data.Number = max(1, min(data.Number, 599999))
        super().__init__(data.Name, data.Number, "DB", data.VariableSections)

        for section in data.VariableSections:
            match section.Name:
                case "Static":
                    self._create_static_section()
                case "Input":
                    self._create_input_section()
                case "InOut":
                    self._create_inout_section()
                case "Output":
                    self._create_output_section()

        self._add_variables()

        for attrib in data.Attributes:
            ET.SubElement(self.AttributeList,
                          attrib).text = data.Attributes[attrib]

        return

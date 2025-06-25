from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from src.modules.XML.Documents import PlcStruct, import_xml
from src.modules.XML.Softwares import Software

@dataclass
class PlcDataType:
    Name: str
    Types: list[PlcStruct]


class XML(Software):
    NAME = "SW.Types.PlcStruct"
    def __init__(self, data: PlcDataType):
        super().__init__(data.Name)

        for udt in data.Types:
            self._add_member(udt.Name, udt.Datatype, udt.attributes)


    def _add_member(self, name: str, datatype: str, attributes: dict):
        Member: ET.Element = ET.SubElement(self.Section, "Member", attrib={
            "Name": name,
            "Datatype": datatype
        })

        if not attributes: return

        AttributeList = ET.SubElement(Member, "AttributeList")
        for attrib in attributes:
            ET.SubElement(AttributeList, "BooleanAttribute", attrib={
                'Name': attrib,
                'SystemDefined': "true"
            }).text = str(attributes[attrib]).lower()


def create(imports: Imports, plc_software: Siemens.Engineering.HW.Software, data: PlcDataType):
    # logging.info(f"Generating {len(data)} User Data Types")
    # logging.debug(f"PlcStruct: {plcstruct}")

    if not data.Name or not data.Types:
        # logging.debug(f"Skipping this PlcStruct...")
        return

    # logging.info(f"Generating UDT {plcstruct.Name}")
    # logging.debug(f"Tags: {plcstruct.Types}")

    xml = XML(data)
    filename: Path = xml.write()
    
    # logging.info(f"Written UDT {plcstruct.Name} XML to: {filename}")

    import_xml(imports, plc_software, filename)

    if filename.exists():
        filename.unlink()

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class PlcTag:
    Name: str
    DataTypeName: str
    LogicalAddress: str

@dataclass
class PlcTagTable:
    DeviceID: int
    Name: str
    Tags: list[PlcTag]


def new(data: PlcTagTable, plc_software: Siemens.Engineering.HW.Software) -> Optional[Siemens.Engineering.SW.Tags.PlcTagTable]:
    if data.Name == "Default tag table": return
    table: Siemens.Engineering.SW.Tags.PlcTagTable = plc_software.TagTableGroup.TagTables.Create(data.Name)

    for tag in data.Tags:
        add_tag(table, tag)

    # logging.info(f"Created Tag Table: {name} ({plc_software.Name} Software)")
    # logging.debug(f"PLC Tag Table: {tag_table.Name}")

    return table

def enumerate_tags(table: Siemens.Engineering.SW.Tags.PlcTagTable) -> list[PlcTag]:
    tags: list[PlcTag] = []
    for tag in table.Tags:
        tags.append(PlcTag(
            Name=tag.Name,
            DataTypeName=tag.DataTypeName,
            LogicalAddress=tag.LogicalAddress
        )
    )

    return tags
    

def find_table(imports: Imports, name: str, plc_software: Siemens.Engineering.HW.Software) -> Siemens.Engineering.SW.Tags.PlcTagTable | None:
    SE: Siemens.Engineering = imports.DLL

    # logging.info(f"Searching Tag Table: {name} in Software {plc_software.Name}...")

    tag_table: Siemens.Engineering.SW.Tags.PlcTagTable = plc_software.TagTableGroup.TagTables.Find(name)

    if not isinstance(tag_table, SE.SW.Tags.PlcTagTable):
        return

    # logging.info(f"Found Tag Table: {name} in {plc_software.Name} Software")
    # logging.debug(f"PLC Tag Table: {tag_table.Name}")

    return tag_table


def add_tag(tag_table: Siemens.Engineering.SW.Tags.PlcTagTable, data: PlcTag) -> Siemens.Engineering.SW.Tags.PlcTag:
    # logging.info(f"Creating Tag: {data.Name} ({tag_table.Name} Table@{data.LogicalAddress} Address)")

    tag: Siemens.Engineering.SW.Tags.PlcTag = tag_table.Tags.Create(data.Name, data.DataTypeName, data.LogicalAddress)

    # logging.info(f"Created Tag: {tag.Name} ({tag_table.Name} Table@{tag.LogicalAddress})")

    return tag

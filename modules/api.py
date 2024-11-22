from __future__ import annotations

from . import logger
from .xml_builder import PlcStruct, OB, FB, GlobalDB, XMLNS, PlcStruct, DocumentSWType
from .config_schema import PlcType, DatabaseType
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging
import tempfile
import uuid
import xml.etree.ElementTree as ET

from modules import config_schema



logger.setup(None, 10)
log = logging.getLogger(__name__)

@dataclass
class Imports:
    DLL: Siemens.Engineering
    DirectoryInfo: System.IO.DirectoryInfo
    FileInfo: System.IO.FileInfo


def get_tia_portal_process_ids(imports: Imports) -> list[int]:
    SE: Siemens.Engineering = imports.DLL

    return [process.Id for process in SE.TiaPortal.GetProcesses()]


def connect_portal(imports: Imports, config: dict[Any, Any], settings: dict[str, Any]) -> Siemens.Engineering.TiaPortal:
    SE: Siemens.Engineering = imports.DLL

    logging.debug(f"config data: {config}")
    logging.debug(f"settings: {settings}")

    connection_method: dict = settings.get('connection_method', {'mode': 'new'})

    if connection_method.get('mode') == 'attach':
        process_id: int|None = connection_method.get("process_id")
        if process_id and isinstance(process_id, int):
            process = SE.TiaPortal.GetProcess(process_id)
            TIA = SE.TiaPortalProcess.Attach(process)

            logging.info(f"Attached TIA Portal Openness ({process.Id}) {process.Mode} at {process.AcquisitionTime}")

            return TIA

    if settings.get('enable_ui', True):
        TIA = SE.TiaPortal(SE.TiaPortalMode.WithUserInterface)
    else:
        TIA = SE.TiaPortal(SE.TiaPortalMode.WithoutUserInterface)

    process = TIA.GetCurrentProcess()

    logging.info(f"Started TIA Portal Openness ({process.Id}) {process.Mode} at {process.AcquisitionTime}")

    return TIA




def create_project(imports: Imports, config: dict[Any, Any], TIA: Siemens.Engineering.TiaPortal) -> Siemens.Engineering.Project:
    DirectoryInfo: DirectoryInfo = imports.DirectoryInfo

    logging.info(f"Creating project {config['name']} at \"{config['directory']}\"...")

    existing_project_path: DirectoryInfo = DirectoryInfo(config['directory'].joinpath(config['name']).as_posix())

    logging.info(f"Checking for existing project: {existing_project_path}")

    if existing_project_path.Exists:

        logging.info(f"{config['name']} already exists...")

        if config['overwrite']:

            logging.info(f"Deleting project {config['name']}...")

            existing_project_path.Delete(True)

            logging.info(f"Deleted project {config['name']}")

        else:
            err = f"Failed creating project. Project already exists ({existing_project_path})"
            logging.error(err)
            raise ValueError

    logging.info("Creating project...")

    project_path: DirectoryInfo = DirectoryInfo(config['directory'].as_posix())

    logging.debug(f"Project Path: {project_path}")

    project_composition: Siemens.Engineering.ProjectComposition = TIA.Projects
    project: Siemens.Engineering.Project = project_composition.Create(project_path, config['name'])

    logging.info(f"Created project {config['name']} at {config['directory']}")

    return project



def import_libraries(imports: Imports, config: dict[Any, Any], TIA: Siemens.Engineering.TiaPortal):
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    for library_data in config.get('libraries', []):

        library_path: FileInfo = FileInfo(library_data.get('path').as_posix())

        logging.info(f"Opening GlobalLibrary: {library_path} (ReadOnly: {library_data.get('read_only')})")

        library: Siemens.Engineering.Library.GlobalLibrary = SE.Library.GlobalLibrary
        if library_data.get('read_only'):
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadOnly) # Read access to the library. Data can be read from the library.
        else:
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadWrite) # Read access to the library. Data can be read from the library.

        logging.info(f"Successfully opened GlobalLibrary: {library.Name}")

    return




def create_devices(config: dict[str, Any], project: Siemens.Engineering.Project) -> list[Siemens.Engineering.HW.Device]:
    devices: list[Siemens.Engineering.HW.Device] = []

    for device_data in config['devices']:
        device_composition: Siemens.Engineering.HW.DeviceComposition = project.Devices
        device: Siemens.Engineering.HW.Device = device_composition.CreateWithItem(device_data['p_typeIdentifier'],
                                                                                  device_data['p_name'],
                                                                                  device_data.get('p_deviceName', '')
                                                                                  )

        logging.info(f"Created device: ({device_data.get('p_deviceName', '')}, {device_data['p_typeIdentifier']}) on {device.Name}")

        devices.append(device)

    return devices

def plug_new_module(module: dict, device_data: dict[str, Any], hw_object: Siemens.Engineering.HW.HardwareObject):
    logging.info(f"Plugging {module['TypeIdentifier']} on [{module['PositionNumber'] + device_data['slots_required']}]...")

    if hw_object.CanPlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'] + device_data['slots_required']):
        hw_object.PlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'] + device_data['slots_required'])

        logging.info(f"{module['TypeIdentifier']} PLUGGED on [{module['PositionNumber'] + device_data['slots_required']}]")

        return

    logging.info(f"{module['TypeIdentifier']} Not PLUGGED on {module['PositionNumber'] + device_data['slots_required']}")

def generate_modules(device_data: dict[str, Any], device: Siemens.Engineering.HW.Device):
    hw_object: Siemens.Engineering.HW.HardwareObject = device.DeviceItems[0]
    for module in device_data.get('Local modules', []):
        plug_new_module(module, device_data, hw_object)

    for module in device_data.get('Modules', []):
        plug_new_module(module, device_data, hw_object)

    return


def find_network_interface_of_device(imports: Imports, device: Siemens.Engineering.HW.Device) -> list[tuple[Siemens.Engineering.HW.Features.NetworkInterface, Siemens.Engineering.HW.DeviceItem]]:
    SE: Siemens.Engineering = imports.DLL

    logging.debug(f"Looking for NetworkInterfaces for Device {device.Name}")

    device_items: Siemens.Engineering.HW.DeviceItem = device.DeviceItems[1].DeviceItems # DeviceItems[1] is used because index 0 is a rack / rail
    network_services: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    for i, item in enumerate(device_items):
        logging.debug(f"Checking if [{i}] DeviceItem {item.Name} is a NetworkInterface")

        network_service: Siemens.Engineering.HW.Features.NetworkInterface = SE.IEngineeringServiceProvider(item).GetService[SE.HW.Features.NetworkInterface]()
        if not network_service:
            logging.debug(f"[{i}] DeviceItem {item.Name} is not a NetworkInterface")
            continue

        logging.debug(f"Found NetworkInterface for DeviceItem {item.Name} at index {i}")

        network_services.append((item, network_service))

    logging.debug(f"Found {len(network_services)} NetworkInterfaces for Device {device.Name}")

    return network_services


def create_device_network_service(imports: Imports, device_data: dict[str, Any], device: Siemens.Engineering.HW.Device) -> list[Siemens.Engineering.HW.Features.NetworkInterface]:
    SE: Siemens.Engineering = imports.DLL

    interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    services: list[tuple[Siemens.Engineering.HW.Features.NetworkInterface, Siemens.Engineering.HW.DeviceItem]] = find_network_interface_of_device(imports, device)
    for service in services:
        device_item: Siemens.Engineering.HW.DeviceItem = service[0]
        network_service: Siemens.Engineering.HW.Features.NetworkInterface = service[1]

        if type(network_service) is SE.HW.Features.NetworkInterface:
            node: Siemens.Engineeering.HW.Node = network_service.Nodes[0]
            data: dict = device_data['network_interface']
            for key, value in data.items():
                if key == "RouterAddress" and value:
                    node.SetAttribute("UseRouter", True)
                    
                node.SetAttribute(key, value)

                logging.info(f"Device {device.Name}'s {key} Attribute set to '{value}'")

            logging.info(f"Network address of {device.Name} has been set to '{node.GetAttribute("Address")}' through {device_item.Name}")

            interfaces.append(network_service)

    return interfaces



def get_plc_software(imports:Imports, device: Siemens.Engineering.HW.Device) -> Siemens.Engineering.HW.Software:
    SE: Siemens.Engineering = imports.DLL

    hw_obj: Siemens.Engineering.HW.HardwareObject = device.DeviceItems

    for device_item in hw_obj:
        logging.debug(f"Accessing a PlcSoftware from DeviceItem {device_item.Name}")

        software_container: Siemens.Engineering.HW.Features.SoftwareContainer = SE.IEngineeringServiceProvider(device_item).GetService[SE.HW.Features.SoftwareContainer]()
        if not software_container:
            logging.debug(f"No PlcSoftware found for DeviceItem {device_item.Name}")
        logging.debug(f"Found PlcSoftware for DeviceItem {device_item.Name}")

        if not software_container:
            continue
        plc_software: Siemens.Engineering.HW.Software = software_container.Software
        if not isinstance(plc_software, SE.SW.PlcSoftware):
            continue

        return plc_software


def generate_tag_tables(device_data: dict[str, Any], plc_software: Siemens.Engineering.HW.Software, tag_source: str = "PLC tags") -> list[Siemens.Engineering.SW.Tags.PlcTagTable]:
    tables: list[Siemens.Engineering.SW.Tags.PlcTagTable] = []
    for data in device_data.get(tag_source, []):
        if data['Name'] == "Default tag table": continue
        tag_table: Siemens.Engineering.SW.Tags.PlcTagTable = create_tag_table(data['Name'], plc_software)
        tables.append(tag_table)

    return tables


def create_tag_table(name: str, plc_software: Siemens.Engineering.HW.Software) -> Siemens.Engineering.SW.Tags.PlcTagTable:
    tag_table: Siemens.Engineering.SW.Tags.PlcTagTable = plc_software.TagTableGroup.TagTables.Create(name)

    logging.info(f"Created Tag Table: {name} ({plc_software.Name} Software)")
    logging.debug(f"PLC Tag Table: {tag_table.Name}")

    return tag_table

def enumerate_tags_in_tag_table(table: Siemens.Engineering.SW.Tags.PlcTagTable) -> list[tuple[str, str, str]]:
    tags: list[tuple[str, str, str]] = []
    for tag in table.Tags:
        tags.append((tag.Name, tag.DataTypeName, tag.LogicalAddress))

    return tags
    

def find_tag_table(imports: Imports, name: str, plc_software: Siemens.Engineering.HW.Software) -> Siemens.Engineering.SW.Tags.PlcTagTable | None:
    SE: Siemens.Engineering = imports.DLL

    logging.info(f"Searching Tag Table: {name} in Software {plc_software.Name}...")

    tag_table: Siemens.Engineering.SW.Tags.PlcTagTable = plc_software.TagTableGroup.TagTables.Find(name)

    if not isinstance(tag_table, SE.SW.Tags.PlcTagTable):
        return

    logging.info(f"Found Tag Table: {name} in {plc_software.Name} Software")
    logging.debug(f"PLC Tag Table: {tag_table.Name}")

    return tag_table


def create_tag(tag_table: Siemens.Engineering.SW.Tags.PlcTagTable, name: str, data_type_name: str, logical_address: str) -> Siemens.Engineering.SW.Tags.PlcTag:
    logging.info(f"Creating Tag: {name} ({tag_table.Name} Table@0x{logical_address} Address)")

    tag: Siemens.Engineering.SW.Tags.PlcTag = tag_table.Tags.Create(name, data_type_name, logical_address)

    logging.info(f"Created Tag: {tag.Name} ({tag_table.Name} Table@0x{tag.LogicalAddress})")

    return tag



def generate_user_data_types(data: dict):
    for plcstruct in data:
        xml = PlcStruct(DocumentSWType.TypesPlcStruct, plcstruct)




def xml_extract_plcstruct(xml: Path) -> list[dict]:
    with open(xml) as file:
        data = file.read()
        weird_char = data[0:3]
        data = data.replace(weird_char, '')

        root = ET.fromstring(data)
        section = root.find(".//ns:Section", {"ns": XMLNS.SECTIONS.value})
        if section is None: return []
        name = root.find(".//Name")
        if name is None: return []
        name = name.text or "User_data_type_1"

        tags: list[dict] = []
        for member in section:
            attribs = member.attrib
            attribs['Datatype'] = attribs['Datatype'].replace('"', r'\"')
            for al in member:
                for el in al:
                    attribs["attributes"] = {el.attrib['Name']: el.text}
            tags.append(attribs)
        
        return tags

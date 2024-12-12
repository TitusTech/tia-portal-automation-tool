from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import logging
import tempfile
import xml.etree.ElementTree as ET

from modules import logger
from modules.structs import XMLNS
from modules.structs import ProjectData
from modules.structs import LibraryData, WireParameter, InstanceParameterTemplate
from modules.structs import DeviceCreationData
from modules.structs import MasterCopiesDeviceData
from modules.structs import ModuleData, ModulesContainerData
from modules.structs import TagData, TagTableData
from modules.structs import InstanceData, LibraryInstanceData
from modules.structs import PlcBlockData, PlcBlockContainer
from modules.structs import PlcStructData
from modules.structs import NetworkSourceData
from modules.structs import NetworkSourceContainer
from modules.structs import GlobalDBData, InstanceContainer, DocumentSWType
from modules.structs import OBData, OBEventClass, FBData
from modules.structs import DatabaseType
from modules.structs import WatchAndForceTablesData,  PlcWatchForceType
from modules.structs import SubnetData
from modules.xml_builder import OB, FB, FC, GlobalDB
from modules.xml_builder import PlcForceTable, PlcWatchTable
from modules.xml_builder import PlcStruct


@dataclass
class Imports:
    DLL: Siemens.Engineering
    DirectoryInfo: System.IO.DirectoryInfo
    FileInfo: System.IO.FileInfo

logger.setup(None, 10)
log = logging.getLogger(__name__)

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




def create_project(imports: Imports, data: ProjectData, TIA: Siemens.Engineering.TiaPortal) -> Siemens.Engineering.Project:
    DirectoryInfo: DirectoryInfo = imports.DirectoryInfo

    logging.info(f"Creating project {data.Name} at \"{data.Directory}\"...")

    existing_project_path: DirectoryInfo = DirectoryInfo(data.Directory.joinpath(data.Name).as_posix())

    logging.info(f"Checking for existing project: {existing_project_path}")

    if existing_project_path.Exists:

        logging.info(f"{data.Name} already exists...")

        if data.Overwrite:

            logging.info(f"Deleting project {data.Name}...")

            existing_project_path.Delete(True)

            logging.info(f"Deleted project {data.Name}")

        else:
            err = f"Failed creating project. Project already exists ({existing_project_path})"
            logging.error(err)
            raise ValueError

    logging.info("Creating project...")

    project_path: DirectoryInfo = DirectoryInfo(data.Directory.as_posix())

    logging.debug(f"Project Path: {project_path}")

    project_composition: Siemens.Engineering.ProjectComposition = TIA.Projects
    project: Siemens.Engineering.Project = project_composition.Create(project_path, data.Name)

    logging.info(f"Created project {data.Name} at {data.Directory}")

    return project



def import_libraries(imports: Imports,
                     TIA: Siemens.Engineering.TiaPortal,
                     data: list[LibraryData]
                     ) -> tuple[list[Siemens.Engineering.Library.GlobalLibrary], list[InstanceParameterTemplate]]:

    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo
    logging.debug(f"Libraries: {data}")

    libraries: list[Siemens.Engineering.Library.GlobalLibrary] = []
    wire_parameters: list[InstanceParameterTemplate] = []
    for library_data in data:
        library_path: FileInfo = FileInfo(library_data.FilePath.as_posix())

        logging.info(f"Opening GlobalLibrary: {library_path} (ReadOnly: {library_data.ReadOnly})")

        library: Siemens.Engineering.Library.GlobalLibrary = SE.Library.GlobalLibrary
        if library_data.ReadOnly:
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadOnly) # Read access to the library. Data can be read from the library.
        else:
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadWrite) # Read access to the library. Data can be read from the library.

        if library_data.Config:
            if library_data.Config.Template:
                with open(library_data.Config.Template) as template_file:
                    template = json.load(template_file)
                    for block in template:
                        w_params = []
                        for param in block.get('parameters', []):
                            instance_params = WireParameter(Name=param.get('name'),
                                                            Section=param.get('section'),
                                                            Datatype=param.get('datatype'),
                                                            Value="",
                                                            Negated=False
                                                            )
                            w_params.append(instance_params)
                        block_param = InstanceParameterTemplate(Name=block.get('block_name'),
                                                            Parameters=w_params
                                                            )
                        wire_parameters.append(block_param)
        libraries.append(library)

        logging.info(f"Successfully opened GlobalLibrary: {library.Name}")

    return libraries, wire_parameters


def get_library(TIA: Siemens.Engineering.TiaPortal, name: str) -> Siemens.Engineering.GlobalLibraries.GlobalLibrary:
    logging.info(f"Searching for Library {name}")
    logging.info(f"List of GlobalLibraries: {TIA.GlobalLibraries}")

    for glob_lib in TIA.GlobalLibraries:
        if glob_lib.Name == name:
            logging.info(f"Found Library {glob_lib.Name}")
            return glob_lib



def clone_mastercopy_to_plc(block_group: Siemens.Engineering.SW.Blocks.PlcBlockGroup, mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopyFolder):
    if not mastercopyfolder: return

    logging.info(f"Cloning Mastercopies of MasterCopyFolder {mastercopyfolder.Name} to PlcBlockGroup {block_group.Name}")

    for folder in mastercopyfolder.Folders:
        if folder.Name == "__": continue # skip unplanned / unknown blocks, let the config handle it
        new_block_group = block_group.Groups.Create(folder.Name)

        logging.info(f"Copied MasterCopyFolder {folder.Name}")

        clone_mastercopy_to_plc(new_block_group, folder)

    for mastercopy in mastercopyfolder.MasterCopies:
        logging.info(f"Copied MasterCopy {mastercopy.Name}")

        block_group.Blocks.CreateFrom(mastercopy)

    return


def generate_mastercopies_to_device(TIA: Siemens.Engineering.TiaPortal, plc_software: Siemens.Engineering.HW.Software, data: MasterCopiesDeviceData):
    logging.info(f"Copying {len(data.Libraries)} Libraries to {plc_software.Name}...")
    logging.debug(f"Libraries: {data.Libraries}")

    for library_name in data.Libraries:
        library: Siemens.Engineering.GlobalLibraries.GlobalLibrary = get_library(TIA, library_name)
        if not library:
            continue
        mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopySystemFolder = library.MasterCopyFolder
        root_block_group: Siemens.Engineering.SW.Blocks.PlcBlockGroup = plc_software.BlockGroup.Groups.Create(library.Name)

        clone_mastercopy_to_plc(root_block_group, mastercopyfolder)

    return



def create_devices(data: list[DeviceCreationData], project: Siemens.Engineering.Project) -> list[Siemens.Engineering.HW.Device]:
    devices: list[Siemens.Engineering.HW.Device] = []

    for device_data in data:
        device_composition: Siemens.Engineering.HW.DeviceComposition = project.Devices
        device: Siemens.Engineering.HW.Device = device_composition.CreateWithItem(device_data.TypeIdentifier, device_data.Name, device_data.DeviceName)

        logging.info(f"Created device: ({device_data.DeviceName}, {device_data.TypeIdentifier}) on {device.Name}")

        devices.append(device)

    return devices

def plug_new_module(module: ModuleData, slots_required: int, hw_object: Siemens.Engineering.HW.HardwareObject):
    logging.info(f"Plugging {module.TypeIdentifier} on [{module.PositionNumber + slots_required}]...")

    if hw_object.CanPlugNew(module.TypeIdentifier, module.Name, module.PositionNumber + slots_required):
        hw_object.PlugNew(module.TypeIdentifier, module.Name, module.PositionNumber + slots_required)

        logging.info(f"{module.TypeIdentifier} PLUGGED on [{module.PositionNumber + slots_required}]")

        return

    logging.info(f"{module.TypeIdentifier} Not PLUGGED on {module.PositionNumber + slots_required}")

def generate_modules(data: ModulesContainerData, device: Siemens.Engineering.HW.Device):
    hw_object: Siemens.Engineering.HW.HardwareObject = device.DeviceItems[0]
    for module in data.LocalModules:
        plug_new_module(module, data.SlotsRequired, hw_object)

    for module in data.HmiModules:
        plug_new_module(module, data.SlotsRequired, hw_object)

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


def generate_tag_tables(data: list[TagTableData], plc_software: Siemens.Engineering.HW.Software) -> list[Siemens.Engineering.SW.Tags.PlcTagTable]:
    tables: list[Siemens.Engineering.SW.Tags.PlcTagTable] = []
    for table_data in data:
        if table_data.Name == "Default tag table": continue
        tag_table: Siemens.Engineering.SW.Tags.PlcTagTable = create_tag_table(table_data.Name, plc_software)
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


def create_tag(tag_table: Siemens.Engineering.SW.Tags.PlcTagTable, data: TagData) -> Siemens.Engineering.SW.Tags.PlcTag:
    logging.info(f"Creating Tag: {data.Name} ({tag_table.Name} Table@{data.LogicalAddress} Address)")

    tag: Siemens.Engineering.SW.Tags.PlcTag = tag_table.Tags.Create(data.Name, data.DataTypeName, data.LogicalAddress)

    logging.info(f"Created Tag: {tag.Name} ({tag_table.Name} Table@{tag.LogicalAddress})")

    return tag



def import_xml(imports: Imports, xml: Path, plc_software: Siemens.Engineering.HW.Software):
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    logging.info(f"Importing XML {xml.absolute()}...")

    xml_path: FileInfo = FileInfo(xml.absolute().as_posix())

    types: Siemens.Engineering.SW.Types.PlcTypeComposition = plc_software.TypeGroup.Types
    types.Import(xml_path, SE.ImportOptions.Override)

    logging.info(f"Imported XML {xml_path}")

    return

def import_xml_to_block_group(imports: Imports,
                              xml_data: str,
                              plc_software: Siemens.Engineering.HW.Software,
                              folder: list[str]
                              ) -> Siemens.Engineering.SW.Blocks.PlcBlock:
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    filename = write_xml(xml_data)

    logging.info(f"Importing XML {filename.absolute()}...")

    xml_path: FileInfo = FileInfo(filename.absolute().as_posix())
    blockgroup = get_folder_of_block_group(plc_software.BlockGroup, folder)
    plcblock: Siemens.Engineering.SW.Blocks.PlcBlock = blockgroup.Blocks.Import(xml_path, SE.ImportOptions.Override)

    logging.info(f"Imported XML {xml_path}")

    return plcblock


def write_xml(xml: str) -> Path:
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as temp:
        filename = Path(temp.name)
        temp.write(xml.encode('utf-8'))

    return filename


def generate_user_data_types(imports: Imports, plc_software: Siemens.Engineering.HW.Software, data: list[PlcStructData] ):
    logging.info(f"Generating {len(data)} User Data Types")

    for plcstruct in data:
        logging.debug(f"PlcStruct: {plcstruct}")

        if not plcstruct.Name or not plcstruct.Types:
            logging.debug(f"Skipping this PlcStruct...")
            continue

        logging.info(f"Generating UDT {plcstruct.Name}")
        logging.debug(f"Tags: {plcstruct.Types}")


        xml = PlcStruct(plcstruct)
        filename: Path = write_xml(xml.xml())
        
        logging.info(f"Written UDT {plcstruct.Name} XML to: {filename}")

        import_xml(imports, filename, plc_software)

        if filename.exists():
            filename.unlink()


def extract_plcstruct_from_xml(xml: Path) -> list[dict]:
    with open(xml) as file:
        file.seek(3)
        data = file.read()
        # weird_char = data[0:3]
        # data = data.replace(weird_char, '')

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

def extract_globaldb_from_xml(imports: Imports,
                              plc_software: Siemens.Engineering.HW.Software,
                              folder: list[str],
                              globaldb_name: str
                              ) -> dict:
    db = get_plc_from_software(plc_software.BlockGroup, folder, globaldb_name)
    if not db: return {}

    compile_single_sw(imports, db)
    xml_data = extract_xml_of_plcblock(imports, db)

    exported_db = {'type': "SW.Blocks.GlobalDB",
                   'name': db.Name,
                   'folder': folder,
                   'data': [],
                   'attributes': {}
                   }
    
    root = ET.fromstring(xml_data)
    section = root.find(".//ns:Section", {"ns": XMLNS.SECTIONS.value})
    if section is None: return {}

    for member in section:
        attribs = member.attrib
        attribs['datatype'] = attribs['Datatype'].replace('"', r'\"')
        for elements in member:
            if elements.tag == "AttributeList":
                for el in elements:
                    attribs["attributes"] = {el.attrib['name']: el.text}
        StartValue = member.find(".//ns:StartValue", {"ns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"})
        if StartValue is not None:
            attribs["StartValue"] = StartValue.text or ""
        exported_db['data'].append(attribs)

    MemoryLayout = root.find(".//MemoryLayout")
    if MemoryLayout is not None:
        exported_db['attributes']['MemoryLayout'] = MemoryLayout.text

    return exported_db

def enumerate_watch_tables_entries(plc_software: Siemens.Engineering.HW.Software) -> list[dict]:
    tables: Siemens.Engineering.SW.WatchAndForceTables.PlcWatchTable = plc_software.WatchAndForceTableGroup.WatchTables

    watch_tables: list[dict] = []

    for watch_table in tables:
        entries: list[dict] = []
        for e in watch_table.Entries:
            entry = {"Name": e.Name,
                    "Address": e.Address,
                     "DisplayFormat": e.DisplayFormat.ToString(),
                     "ModifyIntention": e.ModifyIntention,
                     "ModifyTrigger": e.ModifyTrigger.ToString(),
                     "ModifyValue": e.ModifyValue,
                     "MonitorTrigger": e.MonitorTrigger.ToString()
                    }
            entries.append(entry)
        table = {
            "Name": watch_table.Name,
            "Entries": entries
        }
        watch_tables.append(table)

    return watch_tables

def enumerate_force_tables_entries(plc_software: Siemens.Engineering.HW.Software) -> list[dict]:
    tables: Siemens.Engineering.SW.WatchAndForceTables.PlcForceTable = plc_software.WatchAndForceTableGroup.ForceTables

    force_tables: list[dict] = []
    for force_table in tables:
        entries: list[dict] = []
        for e in force_table.Entries:
            entry = {"Name": e.Name,
                    "Address": e.Address,
                     "DisplayFormat": e.DisplayFormat.ToString(),
                     "ForceIntention": e.ForceIntention,
                     "ForceValue": e.ForceValue,
                     "MonitorTrigger": e.MonitorTrigger.ToString()
                    }
            entries.append(entry)
        table = {
            "Name": force_table.Name,
            "Entries": entries
        }
        force_tables.append(table)

    return force_tables


def compile_single_sw(imports: Imports, plcblock: Siemens.Engineering.SW.Blocks.PlcBlock):
    SE: Siemens.Engineering = imports.DLL

    singleCompile = plcblock.GetService[SE.Compiler.ICompilable]()
    result = singleCompile.Compile()

    return

def extract_xml_of_plcblock(imports: Imports,
                            plcblock: Siemens.Engineering.SW.Blocks.PlcBlock
                            ) -> str:
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    logging.debug(f"Exporting XML of PlcBlock {plcblock.Name}")

    filename = tempfile.mktemp()
    filepath = Path(filename)
    plcblock.Export(FileInfo(filepath.absolute().as_posix()), getattr(SE.ExportOptions, "None"))

    with open(filepath) as file:
        file.seek(3) # get rid of the random weird bytes
        xml_data = file.read()

    filepath.unlink()

    logging.debug(f"Extracted XML: {xml_data}")

    return xml_data

def get_folder_of_block_group(blockgroup: Siemens.Engineering.SW.Blocks.PlcBlockGroup,
                              folder: list[str],
                              make_folders: bool = False
                              )-> Siemens.Engineering.SW.Blocks.BlockGroup:
    logging.debug(f"Current BlockGroup: {blockgroup.Name}")
    logging.debug(f"Remaining Folders: {folder}")

    if len(folder) == 0:
        return blockgroup

    if len(folder[0]) == 0 or (len(folder[0])*" ") == folder[0]:
        return get_folder_of_block_group(blockgroup, folder[1:], make_folders)

    current_blockgroup: Siemens.Engineering.SW.Blocks.PlcBlockGroup | None = blockgroup.Groups.Find(folder[0])
    if not current_blockgroup: 
        if make_folders:
            current_blockgroup = blockgroup.Groups.Create(folder[0])
        else:
            return

    return get_folder_of_block_group(current_blockgroup, folder[1:], make_folders)

def get_plc_from_software(blockgroup: Siemens.Engineering.SW.Blocks.BlockGroup, from_folder: list[str], name: str) -> Siemens.Engineering.SW.Blocks.PlcBlock:
    logging.debug(f"Looking for PlcBlock {name} in BlockGroup {blockgroup.Name} with remaining folders to traverse: {from_folder}")

    if len(from_folder) == 0:
        plc: Siemens.Engineering.SW.Blocks.PlcBlock = blockgroup.Blocks.Find(name)
        if not plc:
            logging.info(f"PlcBlock {name} not found in BlockGroup {blockgroup.Name}")
            return
        logging.info(f"Found: PlcBlock {plc.Name}")
        return plc

    if len(from_folder[0]) == 0:
        return get_plc_from_software(blockgroup, from_folder[1:], name)

    current_blockgroup: Siemens.Engineering.SW.Blocks.PlcBlockGroup | None = blockgroup.Groups.Find(from_folder[0])
    if not current_blockgroup: return

    return get_plc_from_software(current_blockgroup, from_folder[1:], name)


def get_mastercopy_from_folder(mastercopyfolder: Siemens.Engineering.Library.MasterCopies.MasterCopyUserFolder, folder: list[str], name: str) -> Siemens.Engineering.Library.MasterCopies.MasterCopy | None:
    logging.debug(f"Looking for MasterCopy {name} in MasterCopyFolder {mastercopyfolder.Name} with remaining folders to traverse: {folder}")

    if len(folder) == 0:
        mastercopy: Siemens.Engineering.Library.MasterCopies.MasterCopy = mastercopyfolder.MasterCopies.Find(name)

        if not mastercopy:
            logging.info(f"MasterCopy {name} not found in MasterCopyFolder {mastercopyfolder.Name}")
            return 
        logging.info(f"Found: MasterCopy {name}")
        return mastercopy

    if len(folder[0]) == 0:
        return get_mastercopy_from_folder(mastercopyfolder, folder[1:], name)

    current_folder: Siemens.Engineering.Library.MasterCopies.MasterCopyUserFolder | None = mastercopyfolder.Folders.Find(folder[0])
    if not current_folder: return

    return get_mastercopy_from_folder(current_folder, folder[1:], name)

def import_mastercopy_to_software(blockgroup: Siemens.Engineering.SW.Blocks.BlockGroup,
                                  folder: list[str],
                                  mastercopy: Siemens.Engineering.Library.MasterCopies.MasterCopy
                                  ) -> Siemens.Engineering.SW.Blocks.PlcBlock | None:
    logging.debug(f"To add MasterCopy {mastercopy.Name} on PLC {blockgroup.Parent.Parent.GetAttribute("Name")}. {len(folder)} folders remaining ({folder})")

    if len(folder) == 0:
        plcblock: Siemens.Engineering.SW.Blocks.PlcBlock = blockgroup.Blocks.CreateFrom(mastercopy)
        logging.info(f"Inserted PlcBlock {plcblock.Name} into PLC {blockgroup.Parent.Parent.GetAttribute("Name")}")
        return plcblock

    if len(folder[0]) == 0:
        return import_mastercopy_to_software(blockgroup, folder[1:], mastercopy)

    current_group: Siemens.Engineering.SW.Blocks.BlockGroup | None = blockgroup.Groups.Find(folder[0])
    if not current_group:
        current_group = blockgroup.Groups.Create(folder[0])

    return import_mastercopy_to_software(current_group, folder[1:], mastercopy)

def create_database_instance(plc_software: Siemens.Engineering.HW.Software,
                             instance_name: str,
                             database_name: str,
                             number: int,
                             folder: list[str]
                             ) -> Siemens.Engineering.SW.Blocks.InstanceDB:
    db_name = database_name if database_name != "" else f"{instance_name}_DB"
    blockgroup: Siemens.Engineering.SW.Blocks.BlockGroup = get_folder_of_block_group(plc_software.BlockGroup, folder, make_folders=True)
    instance_db: Siemens.Engineering.SW.Blocks.InstanceDB = blockgroup.Blocks.CreateInstanceDB(db_name, True, number, instance_name)

    return instance_db


def create_instance_from_library(TIA: Siemens.Engineering.TiaPortal,
                                 plc_software: Siemens.Engineering.HW.Software,
                                 data: LibraryInstanceData
                                 ) -> Siemens.Engineering.SW.Blocks.PlcBlock | None:
    library: Siemens.Engineering.GlobalLibraries.GlobalLibrary  = get_library(TIA, data.Library)
    if not library:
        logging.info(f"Instance {data.Name} not added to PlcSoftware {plc_software.Name}. GlobalLibrary {data.Library} not found.")
        return

    mastercopy: Siemens.Engineering.Library.MasterCopies.MasterCopy = get_mastercopy_from_folder(library.MasterCopyFolder, data.FromFolder, data.Name)
    if not mastercopy:
        logging.info(f"Instance {data.Name} not added to PlcSoftware {plc_software.Name}. MasterCopy {data.Name} not found.")
        return

    plcblock: Siemens.Engineering.SW.Blocks.PlcBlock | None = import_mastercopy_to_software(plc_software.BlockGroup, data.ToFolder, mastercopy)

    return plcblock

def generate_instances(imports: Imports,
                       TIA: Siemens.Engineering.TiaPortal,
                       plc_software: Siemens.Engineering.HW.Software,
                       instances: list[InstanceData | LibraryInstanceData | PlcBlockData]
                       ) -> list[InstanceContainer | PlcBlockContainer]:
    logging.info(f"Generating Instances: {instances}")

    containers: list[InstanceContainer | PlcBlockContainer] = []

    def _create_and_add_container(block, instance) -> bool:
        if not block:
            return False

        container = InstanceContainer(Name=block.Name,
                                      Type=instance.Type,
                                      Database=instance.Database,
                                      Parameters=instance.Parameters
                                      )
        containers.append(container)

        if "FC" in block.ToString():
            return False
        if instance.Database.Type == DatabaseType.MultiInstance:
            return False
        create_database_instance(plc_software,
                                 block.Name,
                                 instance.Database.Name,
                                 instance.Database.Number,
                                 instance.Database.Folder
                                 )
        return True

    for instance in instances:
        if type(instance) is LibraryInstanceData: # IF type is LIBRARY
            block: Siemens.Engineering.SW.Blocks.PlcBlock = create_instance_from_library(TIA, plc_software, instance)
            if not block:
                continue
            _create_and_add_container(block, instance)

        elif type(instance) is InstanceData: # IF type if LOCAL
            block: Siemens.Engineering.SW.Blocks.PlcBlock = get_plc_from_software(plc_software.BlockGroup, instance.FromFolder, instance.Name)
            if not block:
                logging.info(f"Instance {instance.Name} not added to PlcSoftware {plc_software.Name}. PlcBlock {instance.Name} not found.")
                continue
            _create_and_add_container(block, instance)

        elif type(instance) is PlcBlockData:
            block: Siemens.Engineering.SW.Blocks.PlcBlock = generate_plcblock(imports, TIA, plc_software, instance)
            containers.append(block)

    return containers

def generate_network_sources(imports: Imports,
                             TIA: Siemens.Engineering.TiaPortal,
                             plc_software: Siemens.Engineering.HW.Software,
                             network_sources: list[NetworkSourceData]
                             ) -> list:
    logging.info(f"Generating NetworkSources: {network_sources}")

    containers: list[NetworkSourceContainer] = []
    for block in network_sources:
        instances: list[InstanceContainer | PlcBlockContainer] = generate_instances(imports, TIA, plc_software, block.Instances)
        container = NetworkSourceContainer(Title=block.Title,
                                           Comment=block.Comment,
                                           Instances=instances
                                           )
        containers.append(container)

    logging.debug(f"NetworkSources: {containers}")

    return containers

def generate_plcblock(imports: Imports,
                      TIA: Siemens.Engineering.TiaPortal,
                      plc_software: Siemens.Engineering.HW.Software,
                      block: PlcBlockData
                      ) -> PlcBlockContainer:
    logging.info(f"Generating Program Block: {block}")
    container = PlcBlockContainer(Type=block.Type,
                                  Name=block.Name,
                                  Number=block.Number,
                                  ProgrammingLanguage=block.ProgrammingLanguage,
                                  NetworkSources=[],
                                  Database=block.Database,
                                  Variables=block.Variables,
                                  Parameters=block.Parameters
                                  )
    container.NetworkSources = generate_network_sources(imports, TIA, plc_software, block.NetworkSources)
    match container.Type:
        case DocumentSWType.BlocksOB:
            obdata = OBData(Name=container.Name,
                            Number=container.Number,
                            ProgrammingLanguage=container.ProgrammingLanguage,
                            NetworkSources=container.NetworkSources,
                            Variables=container.Variables,
                            EventClass=OBEventClass.ProgramCycle
                          )
            ob = OB(obdata)
            xml = ob.xml()
            logging.debug(f"Generated OB: {xml}")

        case DocumentSWType.BlocksFB:
            fbdata = FBData(Name=container.Name,
                            Number=container.Number,
                            ProgrammingLanguage=container.ProgrammingLanguage,
                            NetworkSources=container.NetworkSources,
                            Variables=container.Variables
                            )
            fb = FB(fbdata)
            xml = fb.xml()
            logging.debug(f"Generated FB: {xml}")

            import_xml_to_block_group(imports, xml, plc_software, block.Folder)

            if block.Database.Type != DatabaseType.MultiInstance:
                create_database_instance(plc_software, block.Name, block.Database.Name, block.Database.Number, block.Database.Folder)

        case DocumentSWType.BlocksFC:
            print(f"FC to be implemented: {block}")

    
    logging.debug(f"Program Block: {container}")
    return container


def generate_program_blocks(imports: Imports,
                            TIA: Siemens.Engineering.TiaPortal,
                            plc_software: Siemens.Engineering.HW.Software,
                            data: list[PlcBlockData|GlobalDBData]
                            ):
    for block in data:
        if type(block) == PlcBlockData:
            generate_plcblock(imports, TIA, plc_software, block)
        if type(block) == GlobalDBData:
            globaldb = GlobalDB(block)
            xml = globaldb.xml()

            logging.debug(f"Generated GlobalDB: {xml}")

            import_xml_to_block_group(imports, xml, plc_software, block.Folder)

    return

def generate_watch_and_force_tables(imports: Imports, plc_software: Siemens.Engineering.HW.Software, data: list[WatchAndForceTablesData]):
    SE: Siemens.Engineering = imports.DLL
    FileInfo: FileInfo = imports.FileInfo

    for wft in data:
        if wft.Type == PlcWatchForceType.PlcWatchTable:
            wt = PlcWatchTable(wft.Name, wft.Entries)
            xml = wt.xml()

            logging.debug(f"Generated WatchTable: {xml}")

            filename = write_xml(xml)
            xml_path = FileInfo(filename.absolute().as_posix())
            plc_software.WatchAndForceTableGroup.WatchTables.Import(xml_path, SE.ImportOptions.Override)

        if wft.Type == PlcWatchForceType.PlcForceTable:
            wt = PlcForceTable(wft.Name, wft.Entries)
            xml = wt.xml()

            logging.debug(f"Generated ForceTable: {xml}")

            filename = write_xml(xml)
            xml_path = FileInfo(filename.absolute().as_posix())
            plc_software.WatchAndForceTableGroup.ForceTables.Import(xml_path, SE.ImportOptions.Override)

    return


def connect_subnets(itf: Siemens.Engineering.HW.Features.NetworkInterface, data: SubnetData):
    subnet: Siemens.Engineering.HW.Subnet = itf.Nodes[0].CreateAndConnectToSubnet(data.Name)
    io_system: Siemens.Engineering.HW.IoSystem = itf.IoControllers[0].CreateIoSystem(data.IoController)
    return

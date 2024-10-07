from __future__ import annotations

from . import logger
from .config_schema import Plc
from typing import Any
import logging

logger.setup(None, 10)
log = logging.getLogger(__name__)

def execute(SE: Siemens.Engineering, config: dict[Any, Any], settings: dict[str, Any]):
    logging.debug(f"config data: {config}")
    logging.debug(f"settings: {settings}")

    DirectoryInfo = settings['DirectoryInfo']
    FileInfo = settings['FileInfo']

    if settings['enable_ui']:
        TIA = SE.TiaPortal(SE.TiaPortalMode.WithUserInterface)
    else:
        TIA = SE.TiaPortal(SE.TiaPortalMode.WithoutUserInterface)

    current_process = TIA.GetCurrentProcess()

    logging.info(f"Started TIA Portal Openness ({current_process.Id}) {current_process.Mode} at {current_process.AcquisitionTime}")





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



    for library_data in config.get('libraries', []):

        library_path: FileInfo = FileInfo(library_data.get('path').as_posix())

        logging.info(f"Opening GlobalLibrary: {library_path} (ReadOnly: {library_data.get('is_read_only')})")

        library: Siemens.Engineering.Library.GlobalLibrary = SE.Library.GlobalLibrary
        if library_data.get('is_read_only'):
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadOnly) # Read access to the library. Data can be read from the library.
        else:
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadWrite) # Read access to the library. Data can be read from the library.

        logging.info(f"Successfully opened GlobalLibrary: {library.Name}")


    devices: list[Siemens.Engineering.HW.Device] = []
    interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
    for device_data in config['devices']:
        device_composition: Siemens.Engineering.HW.DeviceComposition = project.Devices
        device: Siemens.Engineering.HW.Device = device_composition.CreateWithItem(device_data['p_typeIdentifier'],
                                                                                  device_data['p_name'],
                                                                                  device_data.get('p_deviceName', '')
                                                                                  )

        logging.info(f"Created device: ({device_data.get('p_deviceName', '')}, {device_data['p_typeIdentifier']}) on {device.Name}")

        devices.append(device)
        hw_object: Siemens.Engineering.HW.HardwareObject = device.DeviceItems[0]
        for module in device_data.get('Local modules', []):
            logging.info(f"Plugging {module['TypeIdentifier']} on [{module['PositionNumber'] + device_data['slots_required']}]...")

            if hw_object.CanPlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'] + device_data['slots_required']):
                hw_object.PlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'] + device_data['slots_required'])

                logging.info(f"{module['TypeIdentifier']} PLUGGED on [{module['PositionNumber'] + device_data['slots_required']}]")

                continue

            logging.info(f"{module['TypeIdentifier']} Not PLUGGED on {module['PositionNumber'] + device_data['slots_required']}")

        for module in device_data.get('Modules', []):
            logging.info(f"Plugging {module['TypeIdentifier']} on [{module['PositionNumber'] + device_data['slots_required']}]...")

            if hw_object.CanPlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'] + device_data['slots_required']):
                hw_object.PlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'] + device_data['slots_required'])

                logging.info(f"{module['TypeIdentifier']} PLUGGED on [{module['PositionNumber'] + device_data['slots_required']}]")

                continue

            logging.info(f"{module['TypeIdentifier']} Not PLUGGED on {module['PositionNumber'] + device_data['slots_required']}")

        logging.debug(f"Accessing a DeviceItem Index {1} at Device {device.Name}")

        device_items: Siemens.Engineering.HW.DeviceItem = device.DeviceItems[1].DeviceItems
        for device_item in device_items:
            logging.debug(f"Accessing a NetworkInterface at DeviceItem {device_item.Name}")

            network_service: Siemens.Engineering.HW.Features.NetworkInterface = SE.IEngineeringServiceProvider(device_item).GetService[SE.HW.Features.NetworkInterface]()
            if not network_service:

                logging.debug(f"No NetworkInterface found for DeviceItem {device_item.Name}")

            logging.debug(f"Found NetworkInterface for DeviceItem {device_item.Name}")

            if type(network_service) is SE.HW.Features.NetworkInterface:
                node: Siemens.Engineeering.HW.Node = network_service.Nodes[0]
                node.SetAttribute("Address", device_data['network_address'])

                logging.info(f"Added a network address: {device_data['network_address']}")

                interfaces.append(network_service)

        for device_item in device.DeviceItems:

            logging.debug(f"Accessing a PlcSoftware from DeviceItem {device_item.Name}")

            software_container: Siemens.Engineering.HW.Features.SoftwareContainer = SE.IEngineeringServiceProvider(device_item).GetService[SE.HW.Features.SoftwareContainer]()
            if not software_container:

                logging.debug(f"No PlcSoftware found for DeviceItem {device_item.Name}")

            logging.debug(f"Found PlcSoftware for DeviceItem {device_item.Name}")

            if not software_container: continue
            software_base: Siemens.Engineering.HW.Software = software_container.Software
            if not isinstance(software_base, SE.SW.PlcSoftware): continue

            for tag_table_data in device_data.get('PLC tags', []):
                logging.info(f"Creating Tag Table: {tag_table_data['Name']} ({software_base.Name} Software)")

                tag_table: Siemens.Engineering.SW.Tags.PlcTagTable = software_base.TagTableGroup.TagTables.Create(tag_table_data['Name'])

                logging.info(f"Created Tag Table: {tag_table_data['Name']} ({software_base.Name} Software)")
                logging.debug(f"PLC Tag Table: {tag_table.Name}")

                if not isinstance(tag_table, SE.SW.Tags.PlcTagTable):
                    continue

                for tag_data in tag_table_data['Tags']:
                    logging.info(f"Creating Tag: {tag_data['Name']} ({tag_table.Name} Table@0x{tag_data['LogicalAddress']} Address)")

                    tag_table.Tags.Create(tag_data['Name'], tag_data['DataTypeName'], tag_data['LogicalAddress'])

                    logging.info(f"Created Tag: {tag_data['Name']} ({tag_table.Name} Table@0x{tag_data['LogicalAddress']} Address)")

            for tag_table_data in device_data.get('HMI tags', []):
                pass # to be implemented

            logging.info(f"Adding Program blocks for {software_base.Name}")
            logging.debug(f"Program blocks data: {device_data.get('Program blocks', {})}")

            for plc_block in device_data.get('Program blocks', []):
                if not plc_block.get('source'):
                    match plc_block.get('type'):
                        case Plc.FB:
                            fb: SE.SW.Blocks.PlcBlock = software_base.BlockGroup.Blocks.CreateFB(
                                plc_block.get('name'),
                                True,
                                plc_block.get('number'),
                                getattr(SE.SW.Blocks.ProgrammingLanguage, plc_block.get('programming_language'))
                            )

                            logging.info(f"Added FunctionBlock {fb.Name} to {software_base.Name}")




    subnet: Siemens.Engineering.HW.Subnet = None
    io_system: Siemens.Engineering.HW.IoSystem = None
    for i, network in enumerate(config.get('networks', [])):
        for itf in interfaces:
            if itf.Nodes[0].GetAttribute('Address') != network.get('address'): continue
            if i == 0:

                logging.info(f"Creating ({network.get('subnet_name')} subnet, {network.get('io_controller')} IO Controller)")

                subnet: Siemens.Engineering.HW.Subnet = itf.Nodes[0].CreateAndConnectToSubnet(network.get('subnet_name'))
                io_system: Siemens.Engineering.HW.IoSystem = itf.IoControllers[0].CreateIoSystem(network.get('io_controller'))

                logging.info(f"Successfully created ({network.get('subnet_name')} subnet, {network.get('io_controller')} IO Controller)")
                logging.debug(f"""Subnet: {subnet.Name}
                NetType: {subnet.NetType}
                TypeIdentifier: {subnet.TypeIdentifier}
            IO System: {io_system.Name}
                Number: {io_system.Number}
                Subnet: {io_system.Subnet.Name}""")

                continue

            logging.info(f"Connecting Subnet {subnet.Name} to IoSystem {io_system.Name}")

            itf.Nodes[0].ConnectToSubnet(subnet)

            logging.debug(f"Subnet {subnet.Name} connected to NetworkInterface Subnets")

            if itf.IoConnectors.Count > 0:
                itf.IoConnectors[0].ConnectToIoSystem(io_system)

                logging.info(f"IoSystem {io_system.Name} connected to NetworkInterface IoConnectors")


#!/usr/bin/env python3
# Titus TIA Portal Automation Tool
# Copyright (c) 2025 Titus Global Tech Inc. <titus @ www.titusgt.com>
from __future__ import annotations
import json
import logging
from typing import Any
from pprint import pprint
from pathlib import Path
from dataclasses import dataclass
from schema import Schema, And, Or, Optional


# Previous logger.py
# FORMAT = '%(asctime)s [%(levelname)s] - %(message)s'
FORMAT = '[%(levelname)s] - %(message)s'


class GUIHandler(logging.Handler):
    def __init__(self, textbox):
        super().__init__()
        self.textbox = textbox

    def emit(self, record):
        try:
            message = self.format(record)
            self.textbox.write(f"{message}\n")
        except Exception:
            self.handleError(record)


def setup(textbox=None, LEVEL=20):
    debug = logging.NOTSET
    if LEVEL >= 10:
        debug = logging.DEBUG
    if LEVEL >= 20:
        debug = logging.INFO
    if LEVEL >= 30:
        debug = logging.WARNING
    if LEVEL >= 40:
        debug = logging.ERROR
    if LEVEL >= 50:
        debug = logging.CRITICAL

    logger = logging.getLogger()
    logger.setLevel(debug)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    stdio_handler = logging.StreamHandler()
    stdio_handler.setLevel(debug)
    stdio_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(stdio_handler)

    if textbox:
        gui_handler = GUIHandler(textbox)
        gui_handler.setLevel(debug)
        gui_handler.setFormatter(logging.Formatter(FORMAT))
        logger.addHandler(gui_handler)


# Previous config_schema.py
schema_network = Schema({
        "address": str, # 192.168.0.112
        "subnet_name": str, # Profinet
        "io_controller": str, # PNIO
    })

schema_network_interface = Schema({
    # Optional("Name"): str, # read only
    Optional("Address"): str,
    # Optional("NodeId"): str, # read only
    # Optional("NodeType"): str, # unsupported
    Optional("UseIsoProtocol"): bool,
    Optional("MacAddress"): str,
    Optional("UseIpProtocol"): bool,
    # Optional("IpProtocolSelection"): str, # unsupported
    Optional("Address"): str,
    Optional("SubnetMask"): str,
    # Optional("UseRouter"): bool, # no need, just set RouterAddress to make this true
    Optional("RouterAddress"): str,
    Optional("DhcpClientId"): str,
    Optional("PnDeviceNameSetDirectly"): bool,
    Optional("PnDeviceNameAutoGeneration"): bool,
    Optional("PnDeviceName"): str,
    # Optional("PnDeviceNameConverted"): str, # read only
})

schema_device = {
    "id": int,
    "p_name": str, # PLC1
    "p_typeIdentifier": str, # OrderNumber:6ES7 510-1DJ01-0AB0/V2.0
    Optional("network_interface", default={}): schema_network_interface,
    Optional("required_libraries", default=[]): list[str],
}

schema_device_plc = {
        **schema_device,
        "p_deviceName": str, # NewPlcDevice
        Optional("slots_required", default=2): int,
    }

schema_local_module = Schema({
        "TypeIdentifier": str,
        "device_id": int,
        "PositionNumber": int,
        "Name": str
    })

schema = Schema(
    {
        Optional("overwrite", default=True): bool,
        Optional("devices", default=[]): And(list, [Or(schema_device_plc)]),
        Optional("networks", default=[]): [schema_network],
        Optional("Local modules", default=[]): [schema_local_module],
    },
    ignore_extra_keys=True  
)


# Previous structs.py
@dataclass
class WireParameter:
    Name: str
    Section: str
    Datatype: str
    Value: str | list[str]
    Negated: bool

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

@dataclass
class Imports:
    DLL: Siemens.Engineering
    DirectoryInfo: System.IO.DirectoryInfo
    FileInfo: System.IO.FileInfo


# Previous portal.py
def validate_config(data):
    return schema.validate(data)


def create_modules(module, device): # This function uses TIA Portal Openness API to create (plug) local and HMI modules into a given device. It takes a data container with module details and a TIA Portal Hardware Device object as inputs.
    hw_object = device.DeviceItems[0] # Get the root hardware object of the device (usually the CPU or main rack)
    # pdb.set_trace()
    
    if hw_object.CanPlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber']): # Check if the module can be plugged at the specified position (adjusted by SlotsRequired offset)
        hw_object.PlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber']) # Plug the module into the hardware configuration
        logging.info(f"{module['TypeIdentifier']} PLUGGED on [{module['PositionNumber']}]")
    else:
        logging.info(f"{module['TypeIdentifier']} Not PLUGGED on {module['PositionNumber']}") # Log a message if the module cannot be plugged
    

    # for module in data.HmiModules: # Repeat the same process for HMI-related modules
    #     if hw_object.CanPlugNew(module.TypeIdentifier, module.Name, module.PositionNumber + data.SlotsRequired):
    #         hw_object.PlugNew(module.TypeIdentifier, module.Name, module.PositionNumber + data.SlotsRequired)
    #         logging.info(f"{module.TypeIdentifier} PLUGGED on [{module.PositionNumber + data.SlotsRequired}]")
    #     else:
    #         logging.info(f"{module.TypeIdentifier} Not PLUGGED on {module.PositionNumber + data.SlotsRequired}")


def execute(imports, config, settings):
    # SE = imports.DLL
    TIA = connect_portal(imports, config, settings)

    dev_create_data = [DeviceCreationData(dev.get('p_typeIdentifier', 'PLC_1'), dev.get('p_name', 'NewPLCDevice'), dev.get('p_deviceName', '')) for dev in config.get('devices', [])]
    subnetsdata = [SubnetData(net.get('subnet_name'), net.get('address'), net.get('io_controller')) for net in config.get('networks', [])]

    project = create_project(imports, config, TIA)
    devices = create_devices(dev_create_data, project)
    interfaces = []


    for i, device_data in enumerate(config['devices']):
        device = devices[i]

        for module in config['Local modules']:
            create_modules(module, device)
        # plc_software = get_plc_software(imports, device)

        itf = create_device_network_service(imports, device_data, device)

        for network_interface in itf:
            interfaces.append(network_interface)

    subnet = None
    io_system = None
    for network_interface in interfaces:
        for network in subnetsdata:
            if network_interface.Nodes[0].GetAttribute('Address') != network.Address:
                continue
            if interfaces.index(network_interface) == 0:
                subnet = network_interface.Nodes[0].CreateAndConnectToSubnet(network.Name)
                io_system = network_interface.IoControllers[0].CreateIoSystem(network.IoController)
            else:
                network_interface.Nodes[0].ConnectToSubnet(subnet)
                if network_interface.IoConnectors.Count > 0:
                    network_interface.IoConnectors[0].ConnectToIoSystem(io_system)


setup(None, 10)
log = logging.getLogger(__name__)

def get_tia_portal_process_ids(imports):
    SE = imports.DLL

    return [process.Id for process in SE.TiaPortal.GetProcesses()]


def connect_portal(imports, config, settings):
    SE = imports.DLL

    logging.debug(f"config data: {config}")
    logging.debug(f"settings: {settings}")

    connection_method = settings.get('connection_method', {'mode': 'new'})

    if connection_method.get('mode') == 'attach':
        process_id = connection_method.get("process_id")
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


def create_project(imports, config, TIA):
    DirectoryInfo = imports.DirectoryInfo

    logging.info(f"Creating project {config['name']} at \"{config['directory']}\"...")

    existing_project_path = DirectoryInfo(config['directory'].joinpath(config['name']).as_posix())

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

    project_path = DirectoryInfo(config['directory'].as_posix())

    logging.debug(f"Project Path: {project_path}")

    project_composition = TIA.Projects
    project = project_composition.Create(project_path, config['name'])

    logging.info(f"Created project {config['name']} at {config['directory']}")

    return project


def import_libraries(imports, TIA, data):
    SE = imports.DLL
    FileInfo = imports.FileInfo
    logging.debug(f"Libraries: {data}")

    libraries = []
    wire_parameters = []
    for library_data in data:
        library_path = FileInfo(library_data.FilePath.as_posix())

        logging.info(f"Opening GlobalLibrary: {library_path} (ReadOnly: {library_data.ReadOnly})")

        library = SE.Library.GlobalLibrary
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
                                                            Negated=param.get('negated', False)
                                                            )
                            w_params.append(instance_params)
                        block_param = InstanceParameterTemplate(Name=block.get('block_name'),
                                                            Parameters=w_params
                                                            )
                        wire_parameters.append(block_param)
        libraries.append(library)

        logging.info(f"Successfully opened GlobalLibrary: {library.Name}")

    return libraries, wire_parameters


def get_library(TIA, name):
    logging.info(f"Searching for Library {name}")
    logging.info(f"List of GlobalLibraries: {TIA.GlobalLibraries}")

    for glob_lib in TIA.GlobalLibraries:
        if glob_lib.Name == name:
            logging.info(f"Found Library {glob_lib.Name}")
            return glob_lib


def create_devices(data, project):
    devices = []

    for device_data in data:
        device_composition = project.Devices
        # device = device_composition.CreateWithItem(device_data['TypeIdentifier'], device_data['Name'], device_data['DeviceName'])
        # logging.info(f"Created device: ({device_data['DeviceName']}, {device_data['TypeIdentifier']}) on {device_data['Name']}")
        device: Siemens.Engineering.HW.Device = device_composition.CreateWithItem(device_data.TypeIdentifier, device_data.Name, device_data.DeviceName)
        logging.info(f"Created device: ({device_data.DeviceName}, {device_data.TypeIdentifier}) on {device.Name}")

        devices.append(device)

    return devices


def find_network_interface_of_device(imports, device):
    SE = imports.DLL

    logging.debug(f"Looking for NetworkInterfaces for Device {device.Name}")

    device_items = device.DeviceItems[1].DeviceItems # DeviceItems[1] is used because index 0 is a rack / rail
    network_services = []
    for i, item in enumerate(device_items):
        logging.debug(f"Checking if [{i}] DeviceItem {item.Name} is a NetworkInterface")

        network_service = SE.IEngineeringServiceProvider(item).GetService[SE.HW.Features.NetworkInterface]()
        if not network_service:
            logging.debug(f"[{i}] DeviceItem {item.Name} is not a NetworkInterface")
            continue

        logging.debug(f"Found NetworkInterface for DeviceItem {item.Name} at index {i}")

        network_services.append((item, network_service))

    logging.debug(f"Found {len(network_services)} NetworkInterfaces for Device {device.Name}")

    return network_services


def create_device_network_service(imports, device_data, device):
    SE = imports.DLL

    interfaces = []
    services = find_network_interface_of_device(imports, device)
    for service in services:
        device_item = service[0]
        network_service = service[1]

        if type(network_service) is SE.HW.Features.NetworkInterface:
            node = network_service.Nodes[0]
            data = device_data['network_interface']
            for key, value in data.items():
                if key == "RouterAddress" and value:
                    node.SetAttribute("UseRouter", True)
                    
                node.SetAttribute(key, value)

                logging.info(f"Device {device.Name}'s {key} Attribute set to '{value}'")

            logging.info(f"Network address of {device.Name} has been set to '{node.GetAttribute("Address")}' through {device_item.Name}")

            interfaces.append(network_service)

    return interfaces


def get_plc_software(imports, device):
    SE = imports.DLL

    hw_obj = device.DeviceItems

    for device_item in hw_obj:
        logging.debug(f"Accessing a PlcSoftware from DeviceItem {device_item.Name}")

        software_container = SE.IEngineeringServiceProvider(device_item).GetService[SE.HW.Features.SoftwareContainer]()
        if not software_container:
            logging.debug(f"No PlcSoftware found for DeviceItem {device_item.Name}")
        logging.debug(f"Found PlcSoftware for DeviceItem {device_item.Name}")

        if not software_container:
            continue
        plc_software = software_container.Software
        if not isinstance(plc_software, SE.SW.PlcSoftware):
            continue

        return plc_software
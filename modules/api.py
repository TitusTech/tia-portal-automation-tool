# Titus TIA Portal Automation Tool
# Copyright (c) 2025 Titus Global Tech Inc. <titus @ www.titusgt.com>
# Author: Wineff Gulane
from __future__ import annotations
import json
import logging
from typing import Any
from pprint import pprint
from pathlib import Path
from dataclasses import dataclass
from schema import Schema, And, Or, Optional


# A custom logging handler that sends log messages to a GUI textbox. Takes a textbox object (any object with a write(str) method) as input and writes formatted log messages to it.
# Does not return anything. The textbox must support string input via a write method.
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

# Sets up the logging configuration with optional GUI output. Accepts a textbox object (with a write(str) method) and a logging level (default is INFO/20).
# Configures the root logger to use both the standard output and, if provided, a GUI handler to display logs. Returns nothing.
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


# Schema for a single network configuration.
# Input: dict with required network fields; Return: dict with validated keys.
schema_network = Schema({
    "address": str, # 192.168.0.112
    "subnet_name": str, # Profinet
    "io_controller": str, # PNIO
})

# Schema for a network interface with many optional parameters.
# Input: dict of interface properties; Return: dict with validated optional keys.
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

# Base schema for a device including optional network/interface and libraries.
# Input: dict with device fields; Return: dict with structured device configuration.
schema_device = {
    "id": int,
    "p_name": str, # PLC1
    "p_typeIdentifier": str, # OrderNumber:6ES7 510-1DJ01-0AB0/V2.0
    Optional("network_interface", default={}): schema_network_interface,
    Optional("required_libraries", default=[]): list[str],
}

# Schema for a PLC device, extending base device with extra fields.
# Input: dict; Return: dict with PLC-specific configuration.
schema_device_plc = {
    **schema_device,
    "p_deviceName": str, # NewPlcDevice
    Optional("slots_required", default=2): int,
}

# Schema for a local module configuration associated with a device.
# Input: dict; Return: dict with validated module properties.
schema_local_module = Schema({
    "TypeIdentifier": str,
    "device_id": int,
    "PositionNumber": int,
    "Name": str
})

# Top-level schema containing all devices, networks, and modules.
# Input: dict of configuration; Return: dict with structured project data.
schema = Schema(
    {
        Optional("overwrite", default=True): bool,
        Optional("devices", default=[]): And(list, [Or(schema_device_plc)]),
        Optional("networks", default=[]): [schema_network],
        Optional("Local modules", default=[]): [schema_local_module],
    },
    ignore_extra_keys=True  
)


# Represents a parameter in a wire template, including name, section, and value.
# Input: fields from config or UI; Return: structured WireParameter object.
@dataclass
class WireParameter:
    Name: str
    Section: str
    Datatype: str
    Value: str | list[str]
    Negated: bool

# Template grouping multiple wire parameters under a named instance.
# Input: template name and list of parameters; Return: InstanceParameterTemplate object.
@dataclass
class InstanceParameterTemplate:
    Name: str
    Parameters: list[WireParameter]

# Stores data necessary for creating a new device in the system.
# Input: device type info and names; Return: DeviceCreationData object.
@dataclass
class DeviceCreationData:
    TypeIdentifier: str
    Name: str
    DeviceName: str

# Contains information about a network subnet.
# Input: subnet name, IP address, and IO controller; Return: SubnetData object.
@dataclass
class SubnetData:
    Name: str
    Address: str
    IoController: str

# Represents import references to required DLLs and file system objects.
# Input: DLL reference and file paths; Return: Imports object for later use.
@dataclass
class Imports:
    DLL: Siemens.Engineering
    DirectoryInfo: System.IO.DirectoryInfo
    FileInfo: System.IO.FileInfo


# Validates incoming config data against the predefined schema.
# Input: dict `data`; Return: validated dict or raises error if invalid.
def validate_config(data):
    return schema.validate(data)


# This function uses TIA Portal Openness API to create (plug) local and HMI modules into a given device.
# It takes a data container with module details and a TIA Portal Hardware Device object as inputs.
def create_modules(module, device):
    hw_object = device.DeviceItems[0]
    
    if hw_object.CanPlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber']):
        hw_object.PlugNew(module['TypeIdentifier'], module['Name'], module['PositionNumber'])
        logging.info(f"{module['TypeIdentifier']} PLUGGED on [{module['PositionNumber']}]")
    else:
        logging.info(f"{module['TypeIdentifier']} Not PLUGGED on {module['PositionNumber']}")
    
    # for module in data.HmiModules: # Repeat the same process for HMI-related modules
    #     if hw_object.CanPlugNew(module.TypeIdentifier, module.Name, module.PositionNumber + data.SlotsRequired):
    #         hw_object.PlugNew(module.TypeIdentifier, module.Name, module.PositionNumber + data.SlotsRequired)
    #         logging.info(f"{module.TypeIdentifier} PLUGGED on [{module.PositionNumber + data.SlotsRequired}]")
    #     else:
    #         logging.info(f"{module.TypeIdentifier} Not PLUGGED on {module.PositionNumber + data.SlotsRequired}")


# Executes the automation process to configure devices and networks in TIA Portal.
# Input: imports: DLL and file references, config: Device, module, and network configuration, settings: Optional TIA/project settings
# Return: None; modifies TIA Portal project
def execute(imports, config, settings):
    # Connect to TIA Portal using provided imports and settings
    TIA = connect_portal(imports, config, settings)

    # Extract device and network data from config
    dev_create_data = [
        DeviceCreationData(
            dev.get('p_typeIdentifier', 'PLC_1'),
            dev.get('p_name', 'NewPLCDevice'),
            dev.get('p_deviceName', '')
        )
        for dev in config.get('devices', [])
    ]
    
    subnetsdata = [
        SubnetData(
            net.get('subnet_name'),
            net.get('address'),
            net.get('io_controller')
        )
        for net in config.get('networks', [])
    ]

    # Create or open a project, then add devices
    project = create_project(imports, config, TIA)
    devices = create_devices(dev_create_data, project)

    interfaces = []

    # For each device, plug in modules and configure network interfaces
    for i, device_data in enumerate(config['devices']):
        device = devices[i]

        for module in config['Local modules']:
            create_modules(module, device)

        itf = create_device_network_service(imports, device_data, device)
        interfaces.extend(itf)

    # Connect all interfaces to a common subnet and IO system
    subnet = None
    io_system = None

    for network_interface in interfaces:
        for network in subnetsdata:
            if network_interface.Nodes[0].GetAttribute('Address') != network.Address:
                continue

            if interfaces.index(network_interface) == 0:
                # First matching interface creates subnet and IO system
                subnet = network_interface.Nodes[0].CreateAndConnectToSubnet(network.Name)
                io_system = network_interface.IoControllers[0].CreateIoSystem(network.IoController)
            else:
                # Others join the same subnet and IO system
                network_interface.Nodes[0].ConnectToSubnet(subnet)
                if network_interface.IoConnectors.Count > 0:
                    network_interface.IoConnectors[0].ConnectToIoSystem(io_system)


# Configure logging system with default level and timeout (if used by a custom setup function)
setup(None, 10)
# Create a logger for the current module
log = logging.getLogger(__name__)


# Retrieves the process IDs of all running TIA Portal instances.
# Input: `imports` with DLL reference; Return: list of int process IDs
def get_tia_portal_process_ids(imports):
    SE = imports.DLL
    return [process.Id for process in SE.TiaPortal.GetProcesses()]


# Connects to an existing or new TIA Portal instance using the Openness API.
# Input: imports (DLL), config (dict), settings (dict); Return: TIA portal session object
def connect_portal(imports, config, settings):
    SE = imports.DLL

    logging.debug(f"config data: {config}")
    logging.debug(f"settings: {settings}")

    # Determine connection method: 'attach' to an existing instance or start a new one
    connection_method = settings.get('connection_method', {'mode': 'new'})

    if connection_method.get('mode') == 'attach':
        process_id = connection_method.get("process_id")
        if process_id and isinstance(process_id, int):
            process = SE.TiaPortal.GetProcess(process_id)
            TIA = SE.TiaPortalProcess.Attach(process)
            logging.info(f"Attached TIA Portal Openness ({process.Id}) {process.Mode} at {process.AcquisitionTime}")
            return TIA

    # Create a new TIA Portal instance, with or without UI based on settings
    if settings.get('enable_ui', True):
        TIA = SE.TiaPortal(SE.TiaPortalMode.WithUserInterface)
    else:
        TIA = SE.TiaPortal(SE.TiaPortalMode.WithoutUserInterface)

    process = TIA.GetCurrentProcess()
    logging.info(f"Started TIA Portal Openness ({process.Id}) {process.Mode} at {process.AcquisitionTime}")

    return TIA


# Creates a new TIA Portal project or overwrites an existing one based on configuration.
# Input: imports (with DirectoryInfo), config (project name/path/overwrite flag), TIA instance
# Return: Created TIA project object
def create_project(imports, config, TIA):
    DirectoryInfo = imports.DirectoryInfo

    logging.info(f"Creating project {config['name']} at \"{config['directory']}\"...")

    # Check if project already exists at the given directory
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

    # Create the new project at the target path
    logging.info("Creating project...")
    project_path = DirectoryInfo(config['directory'].as_posix())
    logging.debug(f"Project Path: {project_path}")

    project_composition = TIA.Projects
    project = project_composition.Create(project_path, config['name'])

    logging.info(f"Created project {config['name']} at {config['directory']}")
    return project


# Imports and opens global libraries in TIA Portal and extracts wire parameters from a JSON template if available.
# Input: imports: DLL and FileInfo class for file handling, TIA: TIA Portal session object, data: List of library configurations with optional templates
# Return: libraries: List of opened library objects, wire_parameters: List of InstanceParameterTemplate extracted from templates
def import_libraries(imports, TIA, data):
    SE = imports.DLL
    FileInfo = imports.FileInfo
    logging.debug(f"Libraries: {data}")

    libraries = []
    wire_parameters = []

    for library_data in data:
        library_path = FileInfo(library_data.FilePath.as_posix())

        logging.info(f"Opening GlobalLibrary: {library_path} (ReadOnly: {library_data.ReadOnly})")

        # Open the global library in the specified mode (read-only or read/write)
        library = SE.Library.GlobalLibrary
        if library_data.ReadOnly:
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadOnly)
        else:
            library = TIA.GlobalLibraries.Open(library_path, SE.OpenMode.ReadWrite)

        # If a parameter template is provided, parse it and construct wire parameters
        if library_data.Config and library_data.Config.Template:
            with open(library_data.Config.Template) as template_file:
                template = json.load(template_file)

                for block in template:
                    w_params = []
                    for param in block.get('parameters', []):
                        instance_params = WireParameter(
                            Name=param.get('name'),
                            Section=param.get('section'),
                            Datatype=param.get('datatype'),
                            Value="",
                            Negated=param.get('negated', False)
                        )
                        w_params.append(instance_params)

                    block_param = InstanceParameterTemplate(
                        Name=block.get('block_name'),
                        Parameters=w_params
                    )
                    wire_parameters.append(block_param)

        libraries.append(library)
        logging.info(f"Successfully opened GlobalLibrary: {library.Name}")

    return libraries, wire_parameters


# Searches for a global library in the TIA Portal by name.
# Input: TIA (TIA Portal instance), name (str) - name of the library to find
# Return: Global library object if found, otherwise None
def get_library(TIA, name):
    logging.info(f"Searching for Library {name}")
    logging.info(f"List of GlobalLibraries: {TIA.GlobalLibraries}")

    for glob_lib in TIA.GlobalLibraries:
        if glob_lib.Name == name:
            logging.info(f"Found Library {glob_lib.Name}")
            return glob_lib


# Creates devices in the given TIA Portal project using device creation data.
# Input: data: list of DeviceCreationData objects (TypeIdentifier, Name, DeviceName), project: TIA project object where devices will be added
# Return: List of created device objects
def create_devices(data, project):
    devices = []

    for device_data in data:
        device_composition = project.Devices

        # Create device using TypeIdentifier, Name, and DeviceName
        device: Siemens.Engineering.HW.Device = device_composition.CreateWithItem(
            device_data.TypeIdentifier, device_data.Name, device_data.DeviceName
        )

        logging.info(f"Created device: ({device_data.DeviceName}, {device_data.TypeIdentifier}) on {device.Name}")
        devices.append(device)

    return devices


# Finds network interfaces on a device by inspecting its DeviceItems.
# Input: imports: Contains DLL reference for Siemens API, device: Device object to search for network interfaces
# Return: List of tuples (DeviceItem, NetworkInterface service)
def find_network_interface_of_device(imports, device):
    SE = imports.DLL

    logging.debug(f"Looking for NetworkInterfaces for Device {device.Name}")

    # Skip index 0 (rack/rail), inspect subitems for network interfaces
    device_items = device.DeviceItems[1].DeviceItems
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


# Configures the network interface(s) of a given device based on provided device data.
# Input: imports: Contains DLL reference to Siemens API, device_data: Dict with network interface settings (e.g., Address, SubnetMask), device: The device object to configure
# Return: List of configured NetworkInterface objects
def create_device_network_service(imports, device_data, device):
    SE = imports.DLL
    interfaces = []

    # Retrieve all network interface services of the device
    services = find_network_interface_of_device(imports, device)

    for service in services:
        device_item = service[0]
        network_service = service[1]

        # Ensure the service is a network interface
        if type(network_service) is SE.HW.Features.NetworkInterface:
            node = network_service.Nodes[0]
            data = device_data['network_interface']

            for key, value in data.items():
                if key == "RouterAddress" and value:
                    node.SetAttribute("UseRouter", True)

                node.SetAttribute(key, value)
                logging.info(f"Device {device.Name}'s {key} Attribute set to '{value}'")

            logging.info(
                f"Network address of {device.Name} has been set to '{node.GetAttribute('Address')}' through {device_item.Name}"
            )

            interfaces.append(network_service)

    return interfaces


# Retrieves the PLC software object from a device.
# Input: imports: Contains DLL reference to Siemens API, device: The device object containing PLC hardware
# Return: PlcSoftware object if found, otherwise None
def get_plc_software(imports, device):
    SE = imports.DLL
    hw_obj = device.DeviceItems

    for device_item in hw_obj:
        logging.debug(f"Accessing a PlcSoftware from DeviceItem {device_item.Name}")

        # Attempt to get the SoftwareContainer service for this device item
        software_container = SE.IEngineeringServiceProvider(device_item).GetService[SE.HW.Features.SoftwareContainer]()

        if not software_container:
            logging.debug(f"No PlcSoftware found for DeviceItem {device_item.Name}")
            continue

        logging.debug(f"Found PlcSoftware for DeviceItem {device_item.Name}")

        plc_software = software_container.Software

        # Return only if the software is a valid PlcSoftware instance
        if isinstance(plc_software, SE.SW.PlcSoftware):
            return plc_software